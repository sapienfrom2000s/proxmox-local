# Gateway API

## What it is

Gateway API is the official successor to Ingress. Same Kubernetes SIG built
both.

Ingress only covers hostname/path routing and basic TLS. Everything else —
header matching, traffic splitting, rate limiting, auth — had to be crammed into
controller-specific annotations. Every controller invented its own syntax for
the same features, so switching controllers meant rewriting everything. Gateway
API fixes this by moving those features into the spec as standard fields every
controller must implement the same way.

Concrete example — stripping a path prefix before forwarding:

```
  Nginx:    nginx.ingress.kubernetes.io/rewrite-target: /$2
  Traefik:  traefik.ingress.kubernetes.io/router.middlewares: strip-prefix
  HAProxy:  haproxy.org/path-rewrite: /(.*) /$1
```

Same job, three incompatible syntaxes. Change controllers and every annotation
breaks. Gateway API replaces all three with one standard `pathRewrite` field in
the HTTPRoute spec.

It also splits routing into three layers so different teams manage their own
concerns without stepping on each other.

Concrete example — a single Gateway shared by three app teams:

```
  Cluster Operator
  "I picked Envoy as our controller."
      │
      ▼
  ╭────────────────────────────────────╮
  │ GatewayClass: envoy-gc             │
  ╰────────────────────┬───────────────╯
                       │
  Infrastructure Team
  "I opened port 443 with TLS for *.example.com."
      │
      ▼
  ╭────────────────────────────────────╮
  │ Gateway: main-gw                   │
  │ listener on 443, *.example.com     │
  ╰────────────────────┬───────────────╯
          ┌────────────┼────────────┐
          ▼            ▼            ▼
  ╭──────────────╮ ╭──────────────╮ ╭──────────────╮
  │ App Team A   │ │ App Team B   │ │ App Team C   │
  │ api.example  │ │ shop.example │ │ admin.example│
  │ → API svc    │ │ → frontend   │ │ → admin svc  │
  ╰──────────────╯ ╰──────────────╯ ╰──────────────╯
  each owns their HTTPRoute, doesn't touch the Gateway
```

In Ingress, all three teams would edit the same Ingress resource or each create
their own — either way, the TLS config, port, and controller choice were tangled
together. Gateway API keeps each layer independent.

[High-level comparison with Ingress →](ingress-gateway-api.md)

---

## The three core resources

```
  ┌─────────────────────────────────────────────────┐
  │ GatewayClass                                    │
  │ "Which controller implements this?"             │
  │ (like StorageClass but for networking)          │
  │                                                 │
  │   ┌─────────────────────────────────────────┐   │
  │   │ Gateway                                 │   │
  │   │ "What ports/protocols/hostnames         │   │
  │   │  are open on the infrastructure?"       │   │
  │   │                                         │   │
  │   │   ┌─────────────────────────────────┐   │   │
  │   │   │ HTTPRoute                       │   │   │
  │   │   │ "Which requests go to which     │   │   │
  │   │   │  backend Services, and how?"    │   │   │
  │   │   └─────────────────────────────────┘   │   │
  │   └─────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────┘
```

**GatewayClass** — the cluster operator picks one. It tells Kubernetes which
controller implementation handles the Gateway resources (e.g. Envoy, Istio,
Cilium, Nginx). Only one GatewayClass is needed per controller type.

**Gateway** — the infrastructure team defines this. It opens actual listeners —
ports, protocols, hostnames, TLS config. A Gateway binds to a GatewayClass and
declares what traffic it accepts.

**HTTPRoute** — app teams own these. They attach to a Gateway and define routing
rules — which requests match, and what happens to them.

---

## Why Ingress broke down: the annotation free-for-all

Ingress only covers hostname/path routing and basic TLS. Anything beyond that —
header matching, rate limiting, traffic splitting, rewrites, auth — has to be
done via **annotations** that each controller invents independently.

So `nginx.ingress.kubernetes.io/rewrite-target` is Nginx's way. Traefik has its
own `traefik.ingress.kubernetes.io/` prefix. HAProxy has another. Same feature,
three different annotation strings. Switch controllers and every annotation
breaks.

There's no standard — each controller bolts on features however it wants, and
you're locked to whichever one you chose. Gateway API puts those features into
the spec as normal fields that every conforming controller must implement the
same way.

## What Gateway API adds over Ingress

```
┌──────────────────────┬────────────────┬──────────────────┐
│ Feature              │ Ingress        │ Gateway API      │
├──────────────────────┼────────────────┼──────────────────┤
│ Hostname/path        │ ✓              │ ✓                │
│ Header matching      │ ✗ annotations  │ ✓ standard field │
│ Query param matching │ ✗ annotations  │ ✓ standard field │
│ Weighted split       │ ✗ annotations  │ ✓ standard field │
│ Redirects/rewrites   │ ✗ annotations  │ ✓ standard field │
│ Request mirroring    │ ✗              │ ✓                │
│ TCP/UDP routing      │ ✗              │ ✓ TCPRoute, etc. │
│ gRPC routing         │ ✗              │ ✓ GRPCRoute      │
│ TLS passthrough      │ ✗ annotations  │ ✓ standard mode  │
│ Portable across      │ ✗              │ ✓                │
│   controllers        │                │                  │
└──────────────────────┴────────────────┴──────────────────┘
```

Everything in the right column is a **standard field** — every conforming
controller implements it the same way. No annotations, no vendor lock-in.

---

## Route types beyond HTTP

Gateway API isn't just HTTP. Other route types attach to the same Gateway for
non-HTTP traffic:

- **TCPRoute** — raw TCP proxying (databases, SSH, custom protocols)
- **UDPRoute** — DNS servers, game servers
- **GRPCRoute** — gRPC with method-level routing and status code matching
- **TLSRoute** — TLS passthrough (terminate at the pod, not the gateway)

Each route type is a separate resource. Controllers declare which route types
they support via their GatewayClass.

---

## Cross-namespace routing

In Gateway API, the Gateway lives in one namespace (typically `infra`) and
HTTPRoutes live in app namespaces. By default, a Route can only reference a
Gateway in the same namespace. To cross namespaces, you create a
**ReferenceGrant** — an explicit opt-in that says "namespace X is allowed to
reference resources in namespace Y."

Nothing crosses namespace boundaries without a ReferenceGrant. Secure by
default.

---

## Conformance profiles

Controllers don't all implement every feature. Gateway API defines conformance
profiles so you know what a controller actually supports:

- **Core** — the basics every controller must implement (hostname/path routing,
  simple redirects)
- **Extended** — optional features a controller _may_ implement (header
  matching, weighted splitting, request mirroring)
- **Experimental** — features still being finalized (TCPRoute, UDPRoute,
  GRPCRoute)

Controllers publish which profiles they conform to. This replaces the old "which
annotations does this controller support?" guessing game.

---

## Ingress and Gateway API coexist

Both can run in the same cluster simultaneously. Migration is gradual: create a
Gateway and HTTPRoute for new apps, keep existing Ingress resources working.
There is no cutover moment — they are independent systems sharing the same
underlying entry point (job 1 from
[ingress-gateway-api.md](ingress-gateway-api.md)).
