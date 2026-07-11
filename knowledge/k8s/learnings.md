# K8s Learnings

## 2025-07-09 — K8s vs K3s

### Why K8s over K3s
- K8s is the standard — same API as production clusters (EKS, AKS, GKE)
- Full control over components: containerd, CNI, etcd, kubelet config
- Better learning experience — understanding the real k8s machinery
- More portable — no vendor lock-in to K3s abstractions

### Why not K3s
- K3s abstracts too much — hides the real k8s machinery
- Single binary model is convenient but less educational
- Embedded SQLite default is fragile on power loss (etcd is more resilient)

### Architecture
- 1x Control Plane (cp), 2x Workers (alpha, beta)
- etcd for cluster state (more resilient than SQLite on power loss)
- Containerd as CRI, CNI for networking
