# Kubernetes Networking — Notes

## The foundational rule

Every pod gets its own real IP address — like a mini VM. Not a port mapping, not
a shared address. No NAT between pods, ever, inside the cluster.

Pod IPs are **unique across the entire cluster**, never duplicated across nodes.

## How IPs are carved up

The cluster has one large address range, e.g. `10.244.0.0/16`. Each node is
handed its own slice of it:

```
10.244.0.0/16                 (whole cluster range)
 ├── 10.244.1.0/24  -> Node A
 ├── 10.244.2.0/24  -> Node B
 └── 10.244.3.0/24  -> Node C
```

- **Control plane** (`kube-controller-manager` + `etcd`) has the cluster-wide
  view. It assigns each node its slice when the node joins, and this is the only
  place that knows the full map.
- **Each node's CNI IPAM** hands out individual IPs from its own slice as pods
  get scheduled there. It has no visibility into other nodes — doesn't need it.

## What happens when a pod is scheduled

1. `kubelet` on the target node sees the new pod and starts creating it.
2. It first creates a hidden **pause container** — runs no app code, its only
   job is to hold open a network namespace that all the pod's real containers
   share.
3. `kubelet` calls the **CNI plugin**: "here's a new network namespace, set it
   up."
4. CNI's IPAM assigns the next free IP from the node's slice (e.g. `10.244.2.7`)
   and wires it into that namespace.

The pause container stays alive for the pod's entire lifetime — app containers
can crash and restart without the pod's IP ever changing, because the namespace
never tears down until the whole pod is deleted.

## The veth pair (the "wire")

A veth pair = a virtual patch cable with two ends, always created together.

```
 Pod namespace                 Node's default namespace
 ┌───────────────┐             ┌────────────────┐
 │     eth0      │─────────────│   veth (node   │
 │  10.244.1.4   │  veth pair  │   side end)    │
 └───────────────┘             └────────────────┘
```

- One end sits inside the pod's namespace, appears as `eth0` — this is what the
  pod's IP is assigned to.
- The other end stays on the node, initially unplugged/dangling until connected
  to a bridge.

## Same-node communication: the bridge

The node-side veth ends all plug into a shared virtual switch called the bridge
(commonly `cni0`) — a normal Linux kernel feature, same tech as a real switch.

```
 Node
 ┌───────────────────────────────────────────────────┐
 │  Pod A namespace          Pod B namespace         │
 │ ┌───────────────┐        ┌─────────────-──┐       │
 │ │  eth0         │        │  eth0          │       │
 │ │ 10.244.1.4    │        │ 10.244.1.7     │       │
 │ └───────┬───────┘        └───────┬────────┘       │
 │         │ veth pair              │ veth pair      │
 │ ┌───────▼────────┐        ┌───────▼────────┐      │
 │ │ veth-a (node)  │        │ veth-b (node)  │      │
 │ └───────┬────────┘        └───────┬────────┘      │
 │         └───────────┬─────────────┘               │
 │             ┌───────▼────────┐                    │
 │             │  cni0 bridge   │  (virtual switch)  │
 │             └────────────────┘                    │
 └───────────────────────────────────────────────────┘
```

Pod A -> Pod B: packet leaves A's `eth0`, crosses the veth pair, hits the
bridge, bridge forwards it out the port wired to B — same as a real Ethernet
switch learning MAC/IP-to-port mappings. Never touches the node's physical NIC.

**CNI's role here:** sets this all up once at pod creation (create veth pair,
plug node-side end into the bridge, assign IP) and then steps back. The bridge
itself is just a kernel feature — the OS runs it afterward, no ongoing CNI
involvement needed for basic forwarding.

## Cross-node communication

Problem: Pod B doesn't live on Node A's bridge — it's on a separate machine with
its own separate bridge. The bridge alone can't get a packet there.

### Option A — Native routing

The physical network is taught pod-subnet routes directly.

```
Node A                                              Node B
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│              Pod A              │                 │              Pod B              │
│                │                │                 │                ▲                │
│                ▼                │                 │                │                │
│           cni0 bridge           │                 │           cni0 bridge           │
│                │                │                 │                ▲                │
│                ▼                │                 │                │                │
│      Routing Table Lookup       │                 │      Routing Table Lookup       │
│  Destination: 10.244.2.0/24     │                 │   10.244.2.0/24 = Local Subnet  │
│  Action: via Node B IP (eth0)   │                 │   Action: Deliver to cni0       │
│                │                │                 │                ▲                │
│                ▼                │                 │                │                │
│              eth0               │                 │              eth0               │
└────────────────┬────────────────┘                 └────────────────▲────────────────┘
                 │                                                   │
                 └───────────────► Physical Network ─────────────────┘
                                     (Unwrapped)
```

- Every node's routing table gets populated with "subnet X -> node with real IP
  Y" for every other node in the cluster.
- Distribution mechanism depends on the CNI plugin:
  - **Flannel** — mapping stored centrally (etcd / API), an agent on each node
    watches it and writes local routes.
  - **Calico (BGP mode)** — nodes talk directly via BGP (same protocol real
    internet routers use) and announce their own pod CIDR to peers.
- No wrapping, no per-packet overhead — but needs a physical network that allows
  these custom routes (works well on-prem with router access; not always
  available in restrictive cloud networks).

### Option B — Overlay network (e.g. VXLAN)

Used when the physical network can't be taught pod-subnet routes.

```
Node A                                              Node B
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│     Original Pod A Packet       │                 │      Original Pod A Packet      │
│     src: 10.244.1.4             │                 │     src: 10.244.1.4             │
│     dst: 10.244.2.7             │                 │     dst: 10.244.2.7             │
│                │                │                 │                ▲                │
│                ▼                │                 │                │                │
│       VXLAN Encapsulation       │                 │       VXLAN Decapsulation       │
│  Wraps inner packet in outer    │                 │  Strips away outer host header  │
│  host header: Node A -> Node B  │                 │  to reveal the inner pod packet │
│                │                │                 │                ▲                │
│                ▼                │                 │                │                │
│            eth0 (NIC)           │                 │           eth0 (NIC)            │
└────────────────┬────────────────┘                 └────────────────▲────────────────┘
                 │                                                   │
                 │          Physical Network (Underlay)              │
                 └────────► Only sees Node A IP -> Node B IP ────────┘
```

- Node A wraps the whole original packet inside a new outer packet addressed
  node-to-node (real IPs), sends it over the normal network.
- Node B's CNI agent strips the outer wrapper and hands the original packet to
  its bridge, business as usual.
- Works on any network (physical network never sees pod IPs at all), at the cost
  of a small per-packet encapsulation overhead.

**Which protocol is used?** Decided once, at CNI install time — not negotiated
per-packet. A config file (typically under `/etc/cni/net.d/`) sets the backend
mode (VXLAN, BGP, IP-in-IP, etc.), and every node in the cluster runs the same
CNI plugin with the same mode, so they all agree on how to interpret traffic.
Mixing CNI plugins/modes within one cluster isn't supported for this reason.

## Traffic leaving the cluster (SNAT)

Pod IPs (`10.244.x.x`) are only valid _inside_ the cluster. If a pod sent
traffic to the public internet using its raw pod IP as the source, replies would
have nowhere to route back to.

```
Pod (10.244.1.4)  ──▶  Node rewrites source IP (SNAT)  ──▶  Internet
                        src: 10.244.1.4 -> node's real IP
Reply arrives at node ──▶ node maps it back to the pod ──▶ Pod (10.244.1.4)
```

- The node performs **SNAT**: rewrites the packet's source address to the node's
  own real IP before it leaves the machine.
- To the external service, traffic looks like it's coming from the node, not the
  pod. The node tracks the mapping so replies get routed back to the right pod.
- This only happens for traffic leaving the cluster — pod-to-pod traffic inside
  the cluster is never NAT'd (rule #1).

## Restricting traffic: NetworkPolicy

By default, **every pod can reach every other pod**, cluster-wide, no
restrictions.

A **NetworkPolicy** acts like a firewall rule, but targets pods by **labels**
instead of IPs:

> pods labeled `role=database` may only accept traffic from pods labeled
> `role=backend`, on port 5432. Everything else is dropped.

- NetworkPolicy is just a Kubernetes API object — it does nothing by itself.
- The **CNI plugin** is what actually enforces it, by writing real packet-filter
  rules into the kernel on each node (iptables, eBPF, etc.).
- If your CNI plugin doesn't support NetworkPolicy, the object is accepted but
  silently has no effect — a common surprise.

## Where CNI fits in, end to end

CNI (Container Network Interface) is a **specification/contract**, not a single
running thing. Kubernetes has no built-in networking implementation — it just
calls out to whichever CNI plugin is installed (Flannel, Calico, Cilium, AWS VPC
CNI, etc.) at pod lifecycle events.

Everywhere CNI showed up in this flow:

| Step                      | CNI's role                                                               |
| ------------------------- | ------------------------------------------------------------------------ |
| Pod creation              | Creates veth pair, assigns IP from node's slice, plugs into the bridge   |
| Same-node delivery        | Wired the bridge setup; the bridge itself runs as a kernel feature after |
| Cross-node delivery       | Chooses/implements native routing or overlay; keeps routes in sync       |
| NetworkPolicy enforcement | Writes the actual firewall rules into the kernel per node                |

Pattern: `kubelet` calls CNI at pod create/destroy to set things up, then CNI's
job for that event is done — except for routing sync and NetworkPolicy, where a
persistent per-node agent keeps rules current as pods and policies change.

---
