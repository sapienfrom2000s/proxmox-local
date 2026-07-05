# LVM Storage — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed understanding, or experiments to run.

## Open Questions

- What happens to the thin pool metadata if you create/snapshot hundreds of thin LVs? Is there a formula for sizing the metadata LV relative to the number of expected LVs?
- How does `fstrim` from inside a VM communicate back to the thin pool that blocks are free? Does Proxmox pass TRIM through VirtIO?
- ZFS vs LVM for Proxmox root — when would you choose one over the other? ZFS has built-in checksums, snapshots, compression, but higher RAM usage.

## Half-Formed Understanding

- LVM caching (using an SSD as a cache for an HDD-backed LV) — understand the concept but haven't touched it. `lvcreate --cache` seems to create a cache pool LV + cache LV + origin LV relationship that I don't fully grasp.
- RAID in LVM (`lvcreate --type raid1`) vs mdadm vs hardware RAID — LVM raid1 is convenient but I don't know the performance tradeoffs.

## Experiments to Run

- [ ] Create 50 thin LVs with no data and check metadata utilization with `lvs -a`.
- [ ] Intentionally fill a thin pool and observe behavior — which VM fails first? Does the pool lock up or just the writing VM?
