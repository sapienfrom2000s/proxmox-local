# kube-scheduler

## Why

Kubernetes nodes have varying capacities (CPU, memory, GPU, storage, topology).
Without a scheduler, you'd manually assign every Pod to a node — tedious,
error-prone, and unable to react to cluster changes (node failures, resource
pressure, affinity shifts). The scheduler automates placement decisions so Pods
land on the best-fit node every time.

## What

kube-scheduler is a **control-plane component** that watches for newly created
Pods with no `nodeName` set and assigns them to a suitable node. It does **not**
run containers itself — that's kubelet's job.

## How

The scheduling cycle works in two phases:

### 1. Filtering (Scoring Preparation)

Eliminates nodes that **can't** run the Pod:

- **Node resources** — insufficient CPU/memory
- **Node selector / affinity** — labels don't match
- **Taints & tolerations** — Pod doesn't tolerate node taints
- **Pod topology spread** — constraints violated
- **PersistentVolume binding** — PVC not satisfied
- **Node affinity** — `requiredDuringScheduling` mismatch

### 2. Scoring (Ranking)

Ranks remaining nodes by **preference**:

- **LeastRequestedPriority** — favor nodes with the most free resources
- **BalancedResourceAllocation** — balance CPU/memory usage
- **ImageLocality** — prefer nodes that already have the Pod's container images
  cached
- **InterPodAffinity** — co-locate or spread Pods
- **NodeAffinity** — `preferredDuringScheduling` soft preferences

The node with the **highest score** wins.

### 3. Binding

The scheduler writes a **binding** to the Pod's `spec.nodeName` field. This is
the critical moment — it's an **immutability workaround** (see below).

## Diagram

```
┌─────────────────────────────────────────────────────┐
│                  kube-scheduler                     │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌────────────────┐   │
│  │ Informer │──▶│ Filter   │──▶│   Scoring /    │   │
│  │ (watch)  │   │ Phase    │   │   Ranking      │   │
│  └──────────┘   └──────────┘   └───────┬────────┘   │
│                                        │            │
│                                        ▼            │
│                               ┌────────────────┐    │
│                               │  Bind (PATCH)  │    │
│                               │  spec.nodeName │    │
│                               └───────┬────────┘    │
└───────────────────────────────────────┼─────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  API Server      │
                              │  (Pod object     │
                              │   updated)       │
                              └───────┬──────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        ▼                           ▼
                 ┌─────────────┐            ┌─────────────┐
                 │  Node A     │            │  Node B     │
                 │  kubelet    │            │  kubelet    │
                 │  (runs Pod) │            │             │
                 └─────────────┘            └─────────────┘
```

## Object Immutability & the `nodeName` Patch

`Pod.spec.nodeName` is **immutable after creation** — you cannot `kubectl patch`
or `kubectl edit` it directly. The API server rejects any attempt to change it.

The scheduler bypasses this by **binding** the Pod, which is a special write
operation through the API server's **binding subresource**. Instead of a normal
PATCH:

```bash
# This FAILS — immutability enforced:
kubectl patch pod my-pod -p '{"spec":{"nodeName":"node-2"}}'
# Error: spec.nodeName is immutable

# Scheduler does the equivalent of:
POST /api/v1/namespaces/default/pods/my-pod/binding
{
  "apiVersion": "v1",
  "kind": "Binding",
  "target": {
    "name": "node-2"
  }
}
```

The binding subresource is the **only** mechanism that can set `spec.nodeName`
after creation. It's a deliberate design choice: once a Pod is bound to a node,
**no component** (including the scheduler) can rebind it. If you need to move a
Pod, you must delete and recreate it.

### Why immutability?

- Prevents race conditions (two schedulers fighting over a Pod)
- Makes scheduling decisions **deterministic and atomic**
- kubelet can trust that its assigned Pods won't be yanked away

## Authentication & Authorization

### Authentication (who is calling?)

kube-scheduler authenticates to the API server using one of:

| Method                   | Description                                                                    |
| ------------------------ | ------------------------------------------------------------------------------ |
| **ServiceAccount token** | Mounted automatically at `/var/run/secrets/kubernetes.io/serviceaccount/token` |
| **X.509 client cert**    | If configured via `--tls-cert-file` / `--tls-private-key-file`                 |
| **Kubeconfig**           | `--kubeconfig` flag points to a kubeconfig file with credentials               |

In a standard `kubeadm` cluster, the scheduler uses a **ServiceAccount** with an
auto-mounted token.

### Authorization (what can it do?)

The scheduler needs **minimal permissions**. In RBAC:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: system:kube-scheduler
rules:
  # Read Pods, Nodes, PersistentVolumes, etc.
  - apiGroups: [""]
    resources: ["pods", "nodes", "persistentvolumes"]
    verbs: ["get", "list", "watch"]
  # Write to Pods (binding subresource)
  - apiGroups: [""]
    resources: ["pods/binding"]
    verbs: ["create"]
  # Read PodDisruptionBudgets, StorageClasses, etc.
  - apiGroups: ["policy", "storage.k8s.io"]
    resources: ["poddisruptionbudgets", "storageclasses"]
    verbs: ["get", "list", "watch"]
  # Update Pod status (rare, but used for scheduling condition)
  - apiGroups: [""]
    resources: ["pods/status"]
    verbs: ["patch", "update"]
```

The scheduler **cannot**:

- Delete Pods
- Modify node objects
- Create Deployments/Services
- Access Secrets (beyond what's needed)

### Communication Flow

```
┌──────────────┐  mTLS / ServiceAccount  ┌──────────────┐
│  kube-       │ ◀──────────────────────▶│  kube-       │
│  scheduler   │   watch + bind          │  apiserver   │
└──────────────┘                         └──────────────┘
       │                                         │
       │  reads Pod (no nodeName)                │
       │  reads Nodes, PVs, PDBs                 │
       │                                         │
       └──────── POST /pods/{name}/binding ──────┘
                        │
                        ▼
                 Pod.spec.nodeName
                 is now set ✓
```
