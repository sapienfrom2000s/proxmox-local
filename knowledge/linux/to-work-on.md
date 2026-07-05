# Linux Memory Management — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed understanding, or experiments to run.

## Open Questions

- What's the reclaim latency under direct pressure? If a process does a huge `malloc` and the system has 10Gi of page cache, does it block for microseconds or milliseconds? Depends on LRU list size and whether pages are clean/dirty.
- How does cgroups v2 `memory.high` / `memory.max` interact with page cache reclaim? Does a cgroup-limited container get its own cache evicted before it can allocate, or does it spill into global reclaim?

## Half-Formed Understanding

- `vmtouch` and `fincore` — understand they can query per-file page cache residency but haven't used them in anger.
- `min_free_kbytes` and watermark tuning — vaguely aware that lowering `vm.watermark_scale_factor` can reduce reclaim pressure at the cost of keeping less free memory, but don't know the real-world tradeoffs.

## Experiments to Run

- [ ] Allocate 10Gi of memory on a system with 5Gi free + 10Gi cache, time the allocation, then drop caches and repeat. Compare latency of `malloc` + fault vs direct reclaim.
- [ ] Use `perf` or `bpftrace` to trace `shrink_lruvec` / `shrink_page_list` during a memory pressure event — see which pages get evicted first (file vs anonymous, active vs inactive).
- [ ] Run a VM with a disk-intensive workload, check page cache on the host for the QEMU process's disk image file, then `echo 3 > /proc/sys/vm/drop_caches` and observe if VM performance degrades (it should, briefly, until cache warms up again).
