# K8s Setup

## Swap Disabled Deliberately

Swap is disabled on all k8s nodes. When memory is full, processes are OOM-killed instead of being paged to disk.

Why: paging to disk is orders of magnitude slower than RAM. For a latency-sensitive homelab, crashing fast and restarting is better than silently degrading performance.

- `swapoff -a` and remove swap entries from `/etc/fstab`
- kubelet will refuse to start if swap is detected (unless `--fail-swap-on=false` is set)

## IPv4 Forwarding

Required for pod networking. Enable explicitly for IPv4 only—Kubernetes defaults to IPv4 for inter-pod traffic, and Linux already enables `ipv6.conf.all.forwarding` out of the box.

```sh
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/k8s.conf
sudo sysctl --system
```
