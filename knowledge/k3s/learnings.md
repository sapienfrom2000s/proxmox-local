# K3s Learnings

## 2025-07-09 — K3s vs kubeadm, etcd vs SQLite

### Why K3s over kubeadm
- Lighter — single binary, batteries-included (containerd, CNI, storage), runs on 2GB
- Same Kubernetes API, no lock-in
- Upstream kubeadm needs separate installs for containerd, CNI, ingress, storage

### Why embedded etcd over SQLite
- SQLite corrupts on unclean shutdown (power loss). Auto-backups every 2h, recovery is manual.
- etcd fsyncs WAL per-commit. On restart, replays automatically. Data loss: milliseconds vs hours.
- Cost: ~300MB extra RAM, slightly more disk I/O. Fine on 2GB for homelab.
- Config: `--cluster-init` flag on server install, agents are identical.
