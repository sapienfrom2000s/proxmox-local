# Proxmox — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed understanding, or experiments to run.

## Open Questions

- What happens to linked clones if the template is deleted?
- How do you monitor thin pool data and metadata usage? Is there a CLI command or a dashboard?
- What's the practical difference between `virtio-scsi-pci` and `virtio-blk` for disk performance?

## Half-Formed Understanding

- ZFS vs LVM for Proxmox storage — ZFS has built-in checksumming, snapshots, and compression, but uses more RAM. Not sure when the tradeoff is worth it for a homelab.

## Experiments to Run

- [ ] Create a linked clone vs full clone and compare disk usage with `pvesm status`.
- [ ] Intentionally fill a thin pool and observe what happens — which VMs fail first?
- [ ] See what happens when Cloud-Init runs on a VM that was cloned from a template but then started without the Cloud-Init drive attached.
