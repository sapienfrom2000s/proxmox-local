# kube-proxy — Notes

## 1. The problem it solves

A Service has a stable virtual IP (ClusterIP, e.g. `10.96.0.5`) sitting in front
of a changing set of pods. But nothing actually listens on that IP — no process,
no real device. Something has to intercept a packet headed there and silently
redirect it to a real pod IP behind the Service. That's kube-proxy's job.

```
Pod A                     Service ClusterIP              Real Pods
┌─────────┐               ┌───────────────┐              ┌─────────┐
│ sends to│──────────────>│ 10.96.0.5:80  │<─────┐       │ Pod 1   │
│10.96.0.5│               │ (nobody home) │      │       │ 10.1.1.1│
└─────────┘               └───────────────┘      │       ├─────────┤
                                  │              │       │ Pod 2   │
                                  │ (rewrites)   │       │ 10.1.1.2│
                                  ▼              └───────┤ 10.1.1.3│
                          ┌───────────────┐              └─────────┘
                          │  kube-proxy   │ (traffic redirect)
                          │ (sets rules)  │
                          └───────────────┘
```

## 2. Where it runs, what it watches

- Runs as a pod on **every node** (DaemonSet) — no central decision-maker, each
  instance only handles its own node's traffic.
- Watches the API server for two object types, reacting immediately to changes
  (not polling):
  - **Services** — created / updated / deleted
  - **EndpointSlices** — the live list of real pod IPs behind each Service

```
        API server
   (Services, EndpointSlices)
            │
   ┌────────┼────────┐
   ▼        ▼        ▼
kube-proxy kube-proxy kube-proxy
 (Node A)   (Node B)   (Node C)
   │          │          │
   ▼          ▼          ▼
writes local writes local writes local
kernel rules  kernel rules kernel rules
```

## 3. The core mechanism: destination rewriting

The pod sends a packet to the Service IP (`10.96.0.5`). Before that packet
actually leaves the node, the kernel — using a rule kube-proxy installed —
silently rewrites the destination to a real pod IP (`10.244.1.7`). The sending
pod never sees this; it thinks it's still talking to `10.96.0.5`.

```
Pod A
┌──────────────┐ dst: 10.96.0.5  ┌───────────────────────────┐
│ sends packet │────────────────>│  Kernel (kube-proxy rule) │
└──────────────┘                 │ DNAT: rewrite destination │
                                 └───────────────────────────┘
                                               │
                                               │ dst: 10.244.1.7
                                               ▼
                                      ┌─────────────────┐
                                      │   Backend Pod   │
                                      │ (behind service)│
                                      └─────────────────┘
     Note: Pod A never sees this rewrite happen under the hood.
```

## 4. Picking which pod (iptables mode)

If multiple pods back a Service, the choice is random, weighted evenly across
however many are currently healthy:

```
- 33% chance -> rewrite destination to Pod 1's IP
- 33% chance -> rewrite destination to Pod 2's IP
- 34% chance -> rewrite destination to Pod 3's IP
```

- Implemented via iptables' `statistic` mode: each rule carries a probability,
  checked in order until one matches.
- The pick happens **per new connection**, not per packet — once assigned, every
  packet on that connection keeps going to the same pod.
- Whenever a pod is added/removed, kube-proxy notices via EndpointSlice watches
  and regenerates this probability list.

Organizationally, iptables builds this as a small chain:

```
Packet -> Service ClusterIP:port
   │
   ▼
┌──────────────────┐
│  KUBE-SERVICES   │ Entry point (one rule per Service)
└──────────────────┘ Match on ClusterIP:port -> Jump to KUBE-SVC-XXXX
   │
   ▼
┌──────────────────┐
│  KUBE-SVC-XXXX   │ Load-balancing chain (one per Service)
└──────────────────┘ Weighted-random jump to an endpoint chain
   │
   ▼
┌──────────────────┐
│  KUBE-SEP-AAAA   │ Service EndPoint chain (one per backend pod)
└──────────────────┘ DNAT: rewrite destination to real pod IP:port
   │
   ▼
Packet delivered toward the target pod
```

## 5. iptables mode's scaling limit

Rules are evaluated **top to bottom** — matching cost grows roughly linearly
with the number of Services/rules. Fine at small scale, slow with thousands of
Services.

## 6. IPVS mode — the faster alternative

IPVS (IP Virtual Server) is a purpose-built kernel load balancer — a **hash
table** mapping Service IP:port directly to its backend list, instead of a
sequential rule chain.

```
iptables mode (Sequential)
              ┌─────────┐    ┌─────────┐    ┌─────────┐
Packet ─────> │ Rule #1 │───>│ Rule #2 │───>│ Rule #N │ ───> Match Found!
              └─────────┘    └─────────┘    └─────────┘
              * Slower as the number of rules (Services) grows *

IPVS mode (Hash Table)
              ┌─────────────────────────────┐
Packet ─────> │ Hash Lookup (Service Map)   │ ───> [Direct Backend List]
              └─────────────────────────────┘
              * Consistently fast regardless of Service count *
```

- Lookup time stays roughly constant no matter how many Services exist.
- Supports real algorithms beyond random: round robin, least connections,
  weighted variants.
- Requires IPVS kernel modules loaded — opt-in setting on kube-proxy, not the
  universal default.

## 7. eBPF mode — bypassing kube-proxy's design entirely

iptables and IPVS both intercept packets somewhere in the kernel's normal
netfilter/routing path, after the packet is already built and heading out.
**eBPF** attaches small sandboxed programs directly onto low-level kernel hook
points — as early as the network driver, before most of the normal networking
stack runs at all.

```
Normal Path (iptables/IPVS)
┌────────┐    ┌──────────┐    ┌────────────────┐    ┌─────────┐    ┌───────┐
│ Socket │───>│ IP Stack │───>│netfilter / IPVS│───>│ Routing │───>│  NIC  │
└────────┘    └──────────┘    └────────────────┘    └─────────┘    └───────┘

eBPF Path (e.g., Cilium)
┌────────┐    ┌──────────────────────────────────────────────┐    ┌───────┐
│ Socket │───>│ eBPF Program (rewrites destination instantly)│───>│  NIC  │
└────────┘    └──────────────────────────────────────────────┘    └───────┘
               * Skips netfilter and the chain/hash-table layer entirely *
```

- Tools like **Cilium** replace kube-proxy entirely — same
  Services/EndpointSlice watches, but compiled directly into eBPF programs
  attached at the socket layer or network interfaces. Rewrite can happen as
  early as the pod's socket first connecting.
- Bonus beyond speed: deep hook points give rich per-connection observability
  (which pod talked to which pod, latency, drops) essentially for free —
  iptables and IPVS can't do this since they only see raw packets with no app
  context.

## 8. Quick comparison

```
┌──────────┬──────────────────────┬───────────────────────────────┐
│ Mode     │ Lookup Style         │ Algorithms Available          │
├──────────┼──────────────────────┼───────────────────────────────┤
│ iptables │ Sequential chain walk│ Weighted random only          │
│ IPVS     │ Hash table           │ Round robin, least conn       │
│ eBPF     │ Hooked before stack  │ Fully programmable + obs      │
└──────────┴──────────────────────┴───────────────────────────────┘
```
