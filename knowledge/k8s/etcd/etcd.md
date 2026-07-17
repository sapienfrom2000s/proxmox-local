# etcd

## What etcd is and why Kubernetes can't live without it

Kubernetes is a declarative system. You say "run 3 replicas of nginx" and
Kubernetes figures out where, how, and what to do when things break. But
declarative only works if someone remembers what you asked for. That someone is
etcd.

etcd is the **single source of truth** for the entire cluster. Every Service,
Deployment, ConfigMap, Secret, Node registration, Pod assignment, RBAC policy —
all of it lives in etcd. When `kubectl apply` sends YAML to the API server, the
API server writes it to etcd. When kubelet checks what Pods it should run, it
reads from etcd (via the API server). When a controller notices a Pod died and
creates a replacement, it writes the new Pod to etcd.

**Without etcd, Kubernetes has no memory.** The API server is stateless — it
doesn't cache anything persistently. If etcd disappears, the API server can't
serve read or write requests. The cluster is dead until etcd comes back.

---

## Why not just use a database?

Kubernetes could have used Postgres, MySQL, or even a flat file. It doesn't, for
specific reasons:

**Consistency over availability.** etcd uses the Raft consensus protocol, which
guarantees that every confirmed write is replicated to a majority of nodes
before acknowledged. You never read stale data. In a 3-node cluster, writes
survive the loss of any 1 node. This is a CP system (consistent +
partition-tolerant) in CAP terms — it chooses consistency over availability
during network partitions. For cluster state, that's the right trade: you'd
rather have the API server refuse writes than silently diverge.

**Watch semantics.** Kubernetes controllers don't poll etcd. They set up a
**watch** — a long-lived connection that streams every change as it happens.
When a Pod is created, every controller watching Pods gets notified instantly.
etcd's MVCC (multi-version concurrency control) implementation makes this
efficient: each change gets a revision number, and clients resume from where
they left off. This is how Kubernetes reacts in seconds, not minutes.

**Flat key-value access.** Kubernetes stores everything as objects under a known
key hierarchy: `/registry/pods/<namespace>/<name>`. etcd is a distributed
key-value store — not a document database, not a relational DB. This makes
prefix scans (list all Pods in a namespace) fast and efficient, and it maps
naturally to how Kubernetes organizes its objects.

**Tunable consistency.** etcd supports serializable reads (must go through Raft,
always consistent) and linearizable reads (default — reads the latest confirmed
state). For a system where stale reads can cause cascading failures (scheduling
a Pod on a node that's already removed), this matters.

---

## What etcd actually stores

Everything. Specifically, every Kubernetes object that the API server manages:

```
/registry/
├── pods/
│   └── default/
│       └── nginx-7c4bbc5b4-x2j9k    ← Pod object (YAML→protobuf→bytes)
├── services/
│   └── kube-system/
│       └── kube-dns
├── deployments/
├── configmaps/
├── secrets/                          ← Yes, secrets too (encrypted at rest)
├── nodes/
│   └── alpha                         ← Node status, capacity, conditions
├── serviceaccounts/
├── rolebindings/
└── ...                               ← Every resource type you can kubectl get
```

**What etcd does NOT store:**

- Container images (that's containerd's job on each node)
- Container logs (kubelet exposes them, but they're not in etcd)
- Pod IPs or network state (kube-proxy and CNI handle that)
- Metrics (Prometheus scrapes kubelet and the API server, not etcd)

**Size matters.** etcd has a default storage limit of **2 GB** (configurable up
to 8 GB). This is fine for small-to-medium clusters but can fill up if you store
too many Events (each Pod lifecycle event generates one) or if you leave old
objects lying around. A homelab cluster will never hit this, but it's why
production clusters configure event TTLs.

---

## How etcd works

### Raft consensus

etcd nodes run the **Raft** protocol to agree on the state of the data. Raft is
a consensus algorithm — it's how a group of nodes agrees on a single value even
when some nodes are slow, crash, or get partitioned.

The key concepts:

**Leader election.** One node is the **leader**. All writes go through the
leader. The leader appends the write to its log and replicates it to the other
nodes (**followers**). Once a **majority** (quorum) confirm they've received it,
the leader commits it and acknowledges the write. If the leader dies, the
followers hold an election and a new leader is elected.

**Quorum.** For a cluster of N nodes, you need `(N/2) + 1` nodes to agree. This
means:

| Cluster size | Quorum | Fault tolerance        |
| ------------ | ------ | ---------------------- |
| 1 node       | 1      | 0 (any failure = dead) |
| 3 nodes      | 2      | 1 node can die         |
| 5 nodes      | 3      | 2 nodes can die        |

**Why odd numbers?** A 4-node cluster still needs 3 nodes for quorum — same
fault tolerance as 3 nodes, but more overhead. Always use odd numbers.

**Log replication.** Every write is an entry in the Raft log. The leader appends
it, replicates it, and commits it once quorum confirms. Followers don't apply
the entry until the leader says it's committed. This guarantees every node
applies the same operations in the same order.

## How Kubernetes talks to etcd

The flow is never: client → etcd directly. It's always:

```
kubectl / kubelet / controller
        │
        v
   API Server (only component that talks to etcd)
        │
        v
      etcd
```

**Only the API server touches etcd.** Controllers, kubelet, kube-proxy — none of
them read from etcd directly. They all go through the API server, which handles
authentication, authorization, admission control, and then reads/writes etcd.
This is a deliberate design: the API server is the gatekeeper, and etcd is
hidden behind it.

When you run `kubectl get pods`, the API server reads from etcd, serializes the
result, and returns it. When you `kubectl apply -f deployment.yaml`, the API
server validates the YAML, runs admission webhooks, then writes the object to
etcd.

### The etcd client

The API server talks to etcd via the **etcd client** (clientv3), using gRPC. The
connection is configured with:

- **Endpoints** — `https://127.0.0.1:2379` (etcd always runs on 2379)
- **TLS** — etcd requires mutual TLS (mTLS) in production. The API server
  presents a client cert; etcd verifies it against its trusted CA.
- **Key/cert/CA** — stored in `/etc/kubernetes/pki/etcd/` on the control plane
  node, provisioned by kubeadm.

### What kubeadm does with etcd

When `kubeadm init` runs on the control plane:

1. Generates CA certs for etcd (or reuses existing ones)
2. Generates an etcd server cert (SAN: `localhost`, node IP, node name)
3. Generates a kube-apiserver → etcd client cert
4. Creates the etcd static Pod manifest at `/etc/kubernetes/manifests/etcd.yaml`
5. Kubelet picks up the manifest and starts etcd as a static Pod

The etcd Pod runs with:

- Host networking (or specific port mappings)
- Mounted certs from `/etc/kubernetes/pki/etcd/`
- Data directory at `/var/lib/etcd/`
- Listening on `https://127.0.0.1:2379` (localhost only — only the API server on
  the same machine talks to it)

---

## Single-node etcd vs. clustered etcd

### Single-node (current homelab setup)

Right now, the cluster has one control plane node with one etcd instance. This
works but has a gap: **if that node dies, the entire cluster is gone.** There's
no recovery point — the etcd data is a single copy on one disk.

This is fine for a homelab where the goal is learning, not uptime SLAs.

### Clustered etcd (3-node, the target)

The roadmap (5.2) plans for a 3-node HA control plane with clustered etcd. This
means:

- Each control plane node runs its own etcd instance
- etcd instances form a Raft cluster
- Writes survive the loss of any 1 node
- The API server on each node connects to the local etcd (or all 3)

This is how production clusters (EKS, GKE, AKS) run — etcd is always clustered,
because losing the entire control plane is a catastrophic failure.

The cost: 3 control plane nodes instead of 1, more network traffic between them
(Raft replication), slightly higher write latency (must wait for quorum). For a
homelab, the tradeoff is worth it once you have the hardware.

---

## Why etcd matters for this cluster

The roadmap calls out "etcd for cluster state (more resilient than SQLite on
power loss)" as a reason for choosing k8s over k3s. Here's the full picture:

1. **Power loss resilience.** If a Proxmox host loses power, an etcd with 3
   nodes loses data from 1 node at most — the other 2 have the full state.
   SQLite is a single file — corrupt it and the entire cluster is gone.

2. **The foundation of every future step.** ArgoCD reads/writes through the API
   server → etcd. Ingress rules, storage classes, network policies — everything
   persists in etcd. Understanding how etcd works means understanding why
   cluster state is durable and how to recover it when it isn't.

3. **The gap in the current setup.** A single etcd node means a single disk
   failure or power loss can lose the entire cluster state. The fix is clustered
   etcd (roadmap 5.2), which requires understanding Raft consensus and quorum —
   which is why this doc exists.

---

## Key numbers to remember

| Parameter          | Default | Notes                                        |
| ------------------ | ------- | -------------------------------------------- |
| Client port        | 2379    | API server connects here                     |
| Peer port          | 2380    | etcd-to-etcd cluster communication           |
| Storage quota      | 2 GB    | Hard limit, configurable to 8 GB max         |
| Heartbeat interval | 100ms   | Leader → followers heartbeat                 |
| Election timeout   | 1000ms  | How long before a follower calls an election |
| Max request bytes  | 1.5 MB  | Single object size limit                     |
| Default lease TTL  | varies  | K8s uses node leases (default 40s)           |

---

## Summary

etcd is the cluster's brain. Every Kubernetes object lives there. It uses Raft
consensus to guarantee consistency across nodes, MVCC for efficient watches, and
leases for automatic cleanup. The API server is the only component that talks to
it, and kubeadm handles all the setup as static Pods. For a homelab, the
critical skill is backup/restore — everything else is theoretical until you've
recovered from a snapshot.
