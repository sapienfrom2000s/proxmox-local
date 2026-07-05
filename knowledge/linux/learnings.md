# Linux Memory Management — Learnings

## 2026-07-05

### What is buff/cache?

Run `free -h` and you see three numbers under "used": `used`, `buff/cache`, `available`.

```
               total        used        free      shared  buff/cache   available
Mem:            31Gi       5.1Gi        20Gi       1.2Gi       5.9Gi        24Gi
Swap:          8.0Gi       0.0Ki       8.0Gi
```

**buff/cache** is the sum of two kernel-internal caches:

- **buffers** — raw block device metadata. When the kernel reads/writes a filesystem's block group descriptors, superblock, or inode allocation bitmap, those go through the **buffer cache**. It's the kernel's view of the disk in terms of sectors/blocks, not files. Think of it as "what does the ext4 journal look like on the raw partition?"

- **cached** (page cache) — file data and executable pages stored in memory. When you `cat` a file, write to a log, or `mmap` a shared library, the kernel stores the contents in the **page cache** (4KB pages). Subsequent reads hit RAM instead of disk.

The two caches overlap in modern kernels (the page cache can back filesystem metadata too), but `free` still reports them separately for historical reasons. Most of `buff/cache` is usually the page cache.

### Why is it used?

**Unused RAM is wasted RAM.**

Disk I/O is ~1000x slower than RAM. The kernel's philosophy: if you have free memory, use it to cache disk contents. Every cache hit avoids a disk seek. Over time, the working set of frequently accessed files ends up in RAM.

This is invisible to applications. If an app allocates memory, the kernel drops cache pages instantly (see below). The cache is a fill vacuum, not a reservation.

Scenarios where it helps:
- Re-running the same command (compilation, `ls` on a large directory, `grep`) — file contents are already cached.
- Serving static files from a web server (nginx serves cached file pages without hitting disk).
- VM guests — QEMU's disk images (`qcow2`, raw files on a filesystem) are backed by the page cache. The same blocks read repeatedly by the VM (e.g., database files inside a guest) stay cached on the host.
- `systemd-journald`, logs, databases — any repeated read of the same data.

### Reclaimability

**buff/cache is almost entirely reclaimable.** The kernel can drop clean cache pages at any time — there's no cost beyond a disk read if the page is needed again later.

- **Clean pages** — file contents that match what's on disk. Drop them instantly. No I/O needed, just free the page.
- **Dirty pages** — file contents modified in RAM but not yet written to disk. Can't drop these until they're written back (`pdflush/flusher threads` do this in the background). But they're still counted in `cached` until writeback completes.
- **Page cache** — reclaimable on demand. When the kernel's `kswapd` or `direct reclaim` kicks in, it evicts the least-recently-used (LRU) pages from the page cache first. This is basically free — just bookkeeping.
- **Buffers** — also reclaimable. Buffer cache pages are backed by disk blocks, not file data, but the same mechanism applies: clean = drop, dirty = write then drop.

**How to check:**
```bash
# See what's in the page cache for a specific file
vmtouch /var/log/syslog

# Drop all caches (for testing)
echo 3 > /proc/sys/vm/drop_caches

# Observe reclaimable vs active vs inactive
cat /proc/meminfo | grep -E "(Cache|Active|Inactive|Dirty|Writeback)"
```

**The `available` field** in `free -h` is the key metric. It estimates how much memory is available for new allocations **without causing swapping**. It includes free memory plus reclaimable page cache (minus a safety margin for the kernel's own needs). In the example above, 5.9Gi of buff/cache is almost entirely reclaimable, giving 24Gi available (20Gi free + ~4Gi of cache that can be claimed).

**Important nuance:** The cache doesn't shrink instantly on `malloc`. The kernel does watermark-based reclaim. When free memory hits a low watermark, `kswapd` wakes up and reclaims pages gradually. If allocation is faster than reclaim, `direct reclaim` runs synchronously — the allocating thread blocks until pages are freed. This can cause latency spikes.

### What caused confusion / what fixed it

- Initially confusing that `buff/cache` is both "used" (in the `used` calculation = total - free - buff/cache) but also "available." Fixed by: `used` in `free -h` is a simple arithmetic result (total - free - buff/cache), not a measure of pressure. `available` is the actual "how much can I allocate" number.
- Thought "buffers" and "cached" were separate non-overlapping caches. Fixed by: modern Linux (since ~2.6) merged the page cache and buffer cache internally; `free` reports them separately for compat, but they share the same page structures and a single LRU list.
- Assumed the cache was sticky — that once memory was "used" for cache it couldn't be reclaimed. Fixed by: observing `drop_caches` and running memory-heavy workloads while watching `free -h`; the cache shrinks immediately under pressure.
