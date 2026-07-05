# LVM Storage — Learnings

## 2026-07-05

### Physical Disk

The bottom layer. A physical disk is a block device — `/dev/sda`, `/dev/nvme0n1`, `/dev/mmcblk0`, etc. The OS talks to it via a driver (SATA, NVMe, USB) and sees it as a linear array of fixed-size blocks (usually 512 bytes or 4KB each). No structure yet — just blocks 0 through N.

A 500GB NVMe drive has roughly 1 billion blocks. That's it. No partitions, no files, no filesystem.

### Partition

A partition is a contiguous range of blocks marked off with an entry in the **partition table** (MBR or GPT). The partition table lives in the first few blocks of the disk. Each entry says "starting at block X, ending at block Y, this partition is type `8e00` (Linux LVM)."

Why partition instead of using the whole disk? Three reasons:
1. **Bootloaders** — GRUB needs a tiny BIOS boot partition or an EFI System Partition (ESP) at a fixed location.
2. **Clarity** — `lsblk` shows you exactly what's claimed vs. free. A whole-disk PV looks like the disk is 100% used, masking free space.
3. **Future flexibility** — you can later shrink the PV and create a new partition for something else.

On a typical Proxmox host:

```
nvme0n1       259:0    0 465.8G  0 disk
├─nvme0n1p1   259:1    0  1007K  0 part   # BIOS boot
├─nvme0n1p2   259:2    0   512M  0 part   # EFI System (FAT32)
└─nvme0n1p3   259:3    0 465.3G  0 part   # Linux LVM
```

Only `nvme0n1p3` is available for LVM. The first two are reserved for booting.

### Physical Volume (PV)

`pvcreate /dev/nvme0n1p3` writes an LVM label — 4KB of metadata at the start of the partition that says "this block device is now managed by LVM." The label contains:
- A UUID identifying this specific PV
- The name of the Volume Group it belongs to (empty at first)
- The size of the device in bytes
- A metadata area (small, ~1MB) where LVM stores VG/LV configuration

After `pvcreate`, LVM tracks this device. `pvs` shows it:

```
PV             VG   Fmt  Attr PSize   PFree
/dev/nvme0n1p3      lvm2 ---  465.28g 465.28g
```

No VG yet — it's unallocated.

### Volume Group (VG)

`vgcreate pve /dev/nvme0n1p3` creates a VG named `pve` that claims this PV. The VG metadata is written into the PV's metadata area and replicated across all PVs in the VG (redundancy).

Now LVM knows there's a pool called `pve` with 465.28G of total space, all free.

```
VG   #PV #LV #SN Attr   VSize   VFree
pve    1   0   0 wz--n- 465.28g 465.28g
```

If you add a second disk later, `vgextend pve /dev/sdb1` merges it into the same pool. The VG now spans two physical disks. The LVs can stripe across both, mirror between them, or just fill whichever has space.

Inside the VG, LVM allocates space in **extents** — typically 4MB chunks. Every LV is just a list of extents mapped to physical blocks on the PVs. A 20GB LV is `20 * 1024 / 4 = 5120` extents.

### Logical Volume (LV) — Regular

`lvcreate -n root -L 50G pve` carves 50GB from the pool and names it `root`. This creates:

```
/dev/pve/root  ->  a block device, 50GB
```

This is a **linear LV** — just a contiguous or near-contiguous list of extents. Format it with `mkfs.ext4`, mount it, done. The space is consumed immediately — `lvcreate` reserves all 50GB from the pool.

### Thin Pool

A thin pool is a special kind of LV that enables **thin provisioning**. You create it with:

```bash
lvcreate -L 100G --thinpool data pve
```

This reserves 100GB of physical space from the VG (the pool's "data" space) plus a small chunk for metadata (~1GB, tracks which blocks are actually allocated). But the pool advertises itself as much larger — the default "virtual size" is typically 50-100% of the VG's total free space.

Think of a thin pool as an empty warehouse with 100GB of shelf space, but you tell everyone "you can store up to 1TB here." As long as they don't actually put 1TB of boxes on the shelves, it works. The thin pool tracks which shelves are occupied.

### Thin LV (a VM disk)

When Proxmox creates a VM disk, it runs:

```bash
lvcreate --thinpool pve/data -V 20G -n vm-100-disk-0
```

This creates a **thin LV** — a virtual block device inside the thin pool. It:
- Advertises as 20GB (`-V 20G`)
- Consumes exactly 0 bytes of physical storage initially
- Grows as the VM writes data to the disk
- Shrinks only if explicitly trimmed (TRIM/DISCARD from the guest OS)

Now inside `/dev/pve/data/` (which is the thin pool), there's a thin LV called `vm-100-disk-0`. Proxmox attaches this thin LV to the VM as a SCSI disk.

### What happens with 3 VMs

Create 3 VMs, each with a 20GB disk:

```
Volume Group "pve" - 465GB total
├── Thin pool "data" - 100GB physical, ~400GB virtual
│   ├── Thin LV "vm-100-disk-0" — virtual 20GB, used ~1.5GB (just Debian)
│   ├── Thin LV "vm-101-disk-0" — virtual 20GB, used ~1.5GB
│   └── Thin LV "vm-102-disk-0" — virtual 20GB, used ~1.5GB
├── LV "root" — 50GB (ext4, Proxmox OS)
├── LV "swap" — 8GB
└── LV "data" (that's the thin pool's metadata, ~1GB)
```

**Physical space consumed:** ~4.5GB total (1.5GB × 3 VMs + thin pool metadata). The VG still has ~411GB free.

**What the VMs see:** Each VM sees a 20GB disk attached as `/dev/sda`. Inside the VM, `lsblk` shows 20GB, `df -h` shows 19.6GB available (after formatting with ext4). The VMs have no idea they're sharing a thin pool — the illusion is perfect.

**What `lvs` shows:**

```
LV              VG   Attr       LSize   Pool   Origin  Data%
root            pve  -wi-ao----  50.00g
swap            pve  -wi-ao----   8.00g
data            pve  twi-a-tz-- 100.00g                  3.21%
vm-100-disk-0   pve  Vwi-aotz--  20.00g  data            7.50%
vm-101-disk-0   pve  Vwi-aotz--  20.00g  data            7.50%
vm-102-disk-0   pve  Vwi-aotz--  20.00g  data            7.50%
```

- `Vwi-aotz--` means "Virtual, writable, active, thin, zone"
- `Data%` on each thin LV shows what percentage of its virtual size is physically allocated (7.5% of 20GB = ~1.5GB)
- `Data%` on the thin pool itself shows overall pool utilization (3.21% of 100GB = ~3.2GB total physical used)

**The VM connection:** `qm importdisk` and `qm set --scsi0` are the glue that tells Proxmox "attach thin LV `vm-100-disk-0` to VM ID 100 as a SCSI disk." The VM sees a raw block device, reads/writes to it via VirtIO, and the writes flow through: VirtIO driver → QEMU → LVM thin pool → physical disk blocks. The VM never knows LVM exists.

**Warning scenario:** If the thin pool fills up (all 100GB physical consumed), all 3 VMs freeze simultaneously — not just the one that wrote the most data. The pool doesn't know which VM caused the exhaustion; it just runs out of extents. This is why monitoring thin pool usage (`lvs -o+data_percent`) is critical.

### Full Hierarchy Summary

```
   Physical Disk (e.g. /dev/nvme0n1)
        ↓
   Partition (GPT entry, e.g. /dev/nvme0n1p3)
        ↓
   Physical Volume (pvcreate — LVM label written)
        ↓
   Volume Group (vgcreate — pool of one or more PVs)
        ↓
   Logical Volume (lvcreate — regular, e.g. "root")
        ↓
   OR
        ↓
   Thin Pool (lvcreate --thinpool, e.g. "data")
        ↓
   Thin LV (lvcreate --thinpool -V, e.g. "vm-100-disk-0")
        ↓
   Attached to VM as scsi0 via Proxmox
        ↓
   VM sees /dev/sda (20GB raw block device)
```

## What caused confusion / what fixed it

- Initially confusing that `qm importdisk` copies data into storage but `qm set --scsi0` attaches it — two separate steps. Fixed by: import creates the thin LV, set wires it as a drive in the VM config.
- The thin pool's dual exhaustion modes (data space vs metadata space) wasn't obvious. Fixed by: metadata exhaustion is rarer but more dangerous because it happens with heavy clone/snapshot workflows even when data space is fine. Monitor both with `lvs -o+data_percent,metadata_percent`.
- Didn't realize `local-lvm` in Proxmox is just a label pointing to VG `pve` + thin pool `data`. Fixed by: checking `/etc/pve/storage.cfg` which shows the mapping.
