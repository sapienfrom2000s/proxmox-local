# Ingress vs Gateway API vs MetalLB

## Two jobs, one inbound packet

Every request from outside the cluster has to pass through two gates:

```
INTERNET / LAN
          │
          ▼
  ╭─────────────────╮
  │  1. ENTRY POINT │  L3/L4 — how does the packet reach a node?
  │  (MetalLB,      │  Needs a real IP + open port. Period.
  │   NodePort,     │
  │   hostPort)     │
  ╰────────┬────────╯
           │
           ▼
  ╭─────────────────╮
  │  2. ROUTING     │  L7 — which backend Service handles this?
  │  (Ingress,      │  Matches hostname, path, headers, etc.
  │   Gateway API)  │
  ╰────────┬────────╯
           │
           ▼
         Pods
```

Ingress and Gateway API handle job 2 only. Job 1 is a separate, always-necessary
networking problem. The invariable rule:

> Some node, at some real IP, must have some port open and listening. The only
> choice is which mechanism opens that port.

## Entry point options (solving job 1)

NodePort. Kubernetes picks a random high port (30000–32767) on every node. Works
out of the box, zero extra tooling, but the port is unmemorable and traffic must
target one specific node's IP.

hostPort / hostNetwork. The Ingress controller binds directly to a node's real
interface on a standard port (80/443). Clean URLs, no extra components, but ties
the pod to one node and usually needs elevated privileges.

MetalLB (virtual IP that floats). A dedicated component owns a pool of LAN IPs
and announces one to the network — the same way a printer or router does. If the
node holding it goes down, another picks up the announcement. The only option
giving both a clean address and resilience to node failure.
[Detailed notes →](metallb.md)

```
  ╭────────────────────────────────────────────────────────╮
  │   NodePort          hostPort           MetalLB         │
  │   ─────────         ────────           ───────         │
  │  node:30443         node:443        10.0.0.50:443      │
  │       │                │                  │            │
  │       ▼                ▼                  ▼            │
  │ ╭──────────────╮ ╭──────────────╮ ╭──────────────────╮ │
  │ │  random      │ │  tied to one │ │  floats across   │ │
  │ │  port on     │ │  specific    │ │  all nodes       │ │
  │ │  every node  │ │  node        │ │                  │ │
  │ ╰──────────────╯ ╰──────────────╯ ╰──────────────────╯ │
  ╰────────────────────────────────────────────────────────╯
```

Common mistake: assuming MetalLB is required for Ingress to work. It isn't.
Ingress routes correctly with NodePort or hostPort too. MetalLB only changes
where the open port lives.

## MetalLB in one sentence

Bare-metal clusters have no cloud provider to hand them a load balancer IP.
MetalLB fills that gap: it announces a LAN IP on request. No HTTP awareness, no
routing — just "give me a reachable address."

## Ingress — and why it's frozen

Ingress routes HTTP by hostname/path so many apps can share one entry point. An
Ingress Controller (Nginx, Traefik, etc.) reads the rules and acts as the
reverse proxy.

The problem: the spec only covers hostname/path routing and basic TLS.
Everything else — header matching, traffic splitting, rate limiting, auth — is
bolted on via controller-specific annotations. Switch controllers and you
rewrite everything. The spec is frozen; no new features will ever be added.

## Gateway API — the fix

Gateway API moves the missing features into the spec itself.
[Full breakdown →](gateway-api.md)

```
Ingress                       Gateway API
  ╭───────────────────╮            ╭─────────────────╮
  │ Simple L7 HTTP    │            │  Role-Oriented  │
  │ Routing (Monolith)│            │ (Gateway+Routes)│
  ╰────────┬──────────╯            ╰────────┬────────╯
           │                                │
           ▼                                ▼
  ╭─────────────────╮              ╭─────────────────╮
  │ ✗ No TCP/UDP    │              │ ✓ TCP/UDP/gRPC  │
  │ ✗ Custom Annot. │              │ ✓ Pure Standard │
  │ ✗ Vendor Lock-in│              │ ✓ Multi-Vendor  │
  ╰─────────────────╯              ╰─────────────────╯
```

It also splits one flat resource into three layers — infrastructure, listeners,
and routes — so cluster admins and app teams each manage their own layer
independently.

Same team built both. Gateway API is a strict superset of Ingress, portable, and
actively developed. Both can run side by side, so migration is gradual.

## General lesson

Any system receiving outside traffic needs one thing at the boundary: a
reachable address-and-port that something is actively listening on. Everything
layered on top (HTTP routing, load balancing, canaries, TLS) is a refinement of
what happens after arrival — not a way of avoiding the need for an entry point.
