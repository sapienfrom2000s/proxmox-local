# K8s Setup

## Swap Disabled Deliberately

Swap is disabled on all k8s nodes. When memory is full, processes are OOM-killed instead of being paged to disk.

Why: paging to disk is orders of magnitude slower than RAM. For a latency-sensitive homelab, crashing fast and restarting is better than silently degrading performance.

- `swapoff -a` and remove swap entries from `/etc/fstab`
- kubelet will refuse to start if swap is detected (unless `--fail-swap-on=false` is set)
