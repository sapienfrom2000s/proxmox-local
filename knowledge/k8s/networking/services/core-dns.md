# CoreDNS

## The problem it solves

A Service gives you a stable ClusterIP instead of a throwaway pod IP. But that
IP is still just a number:

- fragile to hardcode (can change if the Service object is deleted/recreated)
- meaningless to read in config — `10.96.0.5` tells you nothing

What you actually want: write `backend-service` in your app's config, and have
something translate that name into the current ClusterIP, automatically. That
translation is CoreDNS's job — the cluster's internal DNS server.

## Where it runs, what it watches

CoreDNS runs as regular pods in `kube-system`, sitting behind its own Service
(traditionally `kube-dns`) with its own stable ClusterIP.

CoreDNS is a regular Deployment, typically with just 2 replicas by default,
scheduled onto whichever nodes the scheduler picks — not one-per-node.

It watches the API server for Service objects, same pattern as kube-proxy:

```
        API server
   (Service objects)
        │
   ┌────┴─────┬─────────────┐
   ▼          ▼             ▼
kube-proxy   CoreDNS       (etc.)
watches ->   watches ->
writes kernel   writes DNS
redirect rules  records
```

kube-proxy and CoreDNS both react to the same Service changes, they just do
different things with that information: kube-proxy programs kernel-level
redirect rules, CoreDNS updates DNS records.

## THE KEY MECHANISM — how a pod even finds CoreDNS

This is the part worth slowing down on: every pod, at creation time, is
automatically told "if you want to look up a name, ask this IP." That IP always
points to CoreDNS.

Compare to your own laptop: somewhere in your network settings there's a "DNS
server" IP, used automatically every time you type a website name. Kubernetes
does the exact same thing for every pod — instead of your ISP's DNS server, it
points to CoreDNS.

`kubelet` writes this automatically into every pod, one file, one line:

```
 Pod's /etc/resolv.conf   (auto-injected by kubelet, no manual setup)
┌──────────────────────────────────────┐
│ nameserver 10.96.0.10                │  <- CoreDNS's Service ClusterIP
│ search my-namespace.svc.cluster.local│
│        svc.cluster.local             │
│        cluster.local                 │
└──────────────────────────────────────┘
```

No app or developer configures this by hand. When the app inside the pod does a
normal DNS lookup — whatever language it's written in — the OS just reads this
file like on any regular Linux machine, and queries `10.96.0.10`.

## The naming scheme

CoreDNS gives every Service a predictable name, built from fixed parts:

```
 my-service . my-namespace . svc . cluster.local
     │             │          │        │
     │             │          │        └─ cluster's root DNS domain (fixed)
     │             │          └─ literal "svc" — marks this as a Service
     │             └─ the namespace the Service lives in
     └─ the Service's own name (from its YAML)
```

Example: a Service `backend-service` in namespace `payments` automatically gets
the name `backend-service.payments.svc.cluster.local`, resolving to that
Service's ClusterIP — no manual DNS record created by hand.

Shortcut: because of the `search` list in `/etc/resolv.conf`, a pod _inside_
`payments` can just write `backend-service` and the OS auto-appends the rest. A
pod in a _different_ namespace needs at least `backend-service.payments`.

## How a lookup resolves, step by step

```
Pod (in "payments" namespace)
   │
   │ Looks up "backend-service"
   ▼
┌──────────────────────────────────────────────┐
│            Read /etc/resolv.conf             │
│ Search domain appended:                      │
│ backend-service.payments.svc.cluster.local   │
│ Nameserver targeted: 10.96.0.10              │
└──────────────────────────────────────────────┘
   │
   │ Sends DNS query
   ▼
┌──────────────────────────────────────────────┐
│         CoreDNS Pod (10.96.0.10)             │
│ Checks internal records built from watching  │
│ the Kubernetes API server                    │
└──────────────────────────────────────────────┘
   │
   │ Replies with ClusterIP: 10.96.0.7
   ▼
┌──────────────────────────────────────────────┐
│           Pod Receives ClusterIP             │
│ Resolves name to 10.96.0.7                   │
└──────────────────────────────────────────────┘
   │
   │ Sends actual data traffic to 10.96.0.7
   ▼
┌──────────────────────────────────────────────┐
│          Kernel DNAT (kube-proxy)            │
│ Intercepts and rewrites destination IP       │
│ from ClusterIP to a real Backend Pod IP      │
└──────────────────────────────────────────────┘
   │
   │ Traffic routed across overlay
   ▼
 Target Pod (Backend Endpoint)
```

Two separate steps, worth keeping apart:

1. **DNS lookup** — name -> ClusterIP (CoreDNS's job, once per connection setup,
   usually cached briefly)
2. **Traffic routing** — ClusterIP -> real pod IP (kube-proxy's job, on every
   packet, via the kernel rule)

CoreDNS never touches actual application traffic — it only ever answers the
initial "what's the IP for this name" question.

## Pod lookups vs Service lookups (headless Services)

Normally, a Service name resolves to one ClusterIP — the stable virtual IP,
load-balanced by kube-proxy. Sometimes an app needs to know about _each
individual pod_ behind a Service instead — e.g. a database cluster (Cassandra,
Kafka) where each replica has a distinct identity and clients must connect to
specific ones, not a randomly load-balanced one.

Create a Service with `clusterIP: None` — a **headless Service** — and CoreDNS
changes behavior for that name entirely:

```
Normal Service Lookup                  Headless Service Lookup
  (backend-service.payments.svc...)      (clusterIP: None)
             │                                      │
             ▼                                      ▼
     ┌───────────────┐                      ┌───────────────┐
     │   10.96.0.7   │                      │  10.244.1.4   │
     └───────────────┘                      │  10.244.2.9   │
      One ClusterIP                         │  10.244.3.2   │
                                            └───────────────┘
     Traffic is sent to the virtual         Returns direct A/AAAA records
     IP, then load-balanced down            for every ready Pod. The client
     to individual pods by kube-proxy       handles routing and picking
     rules inside the kernel.               backends, skipping kube-proxy.
```

A second form: pods managed by a StatefulSet behind a headless Service each get
their **own** unique DNS name, e.g.:

```
backend-service-0.backend-service.payments.svc.cluster.local
    -> always resolves to that exact replica's pod IP
```

This is the one place DNS resolution bypasses kube-proxy's load-balancing
entirely — the app itself picks which pod IP (from CoreDNS's list) to use.
