# MetalLB

### The Real Problem it Solves

Kubernetes is designed to run in the cloud (like AWS or Google Cloud). In the
cloud, when you create a public-facing application, the cloud provider
automatically spins up a massive, external hardware Load Balancer to give your
app a single, clean entry IP address.

However, when you run Kubernetes on your own physical hardware (Bare Metal or a
Homelab), there is no cloud provider to give you a load balancer.

Without a load balancer:

- Your applications are trapped inside an internal, isolated cluster network.
- External devices on your home or office LAN have no way to reach them
  directly.

### What MetalLB Does

MetalLB is a software-defined load balancer built specifically for bare-metal
clusters. It watches for Services of type `LoadBalancer` and assigns them an IP
from a configured pool. It mimics a cloud load balancer inside your private
network:

1. Allocates a Local Address: It hooks into your physical LAN and takes a clean,
   unused IP address from your local network pool.
2. Binds to a Healthy NIC: It temporarily attaches (binds) this new IP address
   to the physical network card (NIC) of a healthy server in your cluster.
3. Resilient Routing: If that server dies, MetalLB instantly moves that exact
   same IP address to the NIC of another healthy server.

### Why It's the "Only Clean Option"

Without MetalLB, you would have to expose your applications using clunky
workarounds like `NodePort` (which forces users to type in random high-number
ports like `site.local:31082`). MetalLB gives you standard, clean access on
ports 80 and 443 with automatic failover.

MetalLB does this by creating a Virtual IP (VIP) that floats dynamically above
the nodes. Instead of being permanently tied to one physical NIC, MetalLB
temporarily binds this VIP to a healthy node's NIC and dynamically shifts it to
a backup node's NIC if the primary node goes down.

```
  Node 1 (ACTIVE)          Node 2 (BACKUP)
  holds VIP 192.168.1.200  ready to take over
       │                         │
       └──────────┬──────────────┘
                  │
        MetalLB announces VIP
        to the local network
```

If Node 1 crashes, MetalLB instantly shifts the VIP to Node 2. The IP never
changes, so DNS records and clients never notice.

Without MetalLB, a node failure means manually updating DNS or telling users to
type a different address.

---

## Homelab setup

### 1. IP pool

You give MetalLB a range of private IPs from your LAN (e.g.
`192.168.1.200–250`). The range is just a pool — MetalLB hands out addresses one
at a time to different apps. DNS does NOT point to the whole range.

### 2. DNS points to the specific VIP

Your local DNS (Pi-hole, AdGuard, etc.) resolves your domain to the single VIP
MetalLB assigned to that app:

```
  Pi-hole:  site.local → 192.168.1.200
                        │
                        ▼
              MetalLB VIP (floating)
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
          Node 1 [ACTIVE]    Node 2 [BACKUP]
          holds the IP       ready to take over
```

---

## What happens when traffic actually arrives

MetalLB only announces the VIP to the network — it doesn't touch the packet
itself. The moment the packet reaches the node holding the VIP, kube-proxy takes
over.

kube-proxy has already written iptables (or IPVS) rules on every node saying:
"traffic destined for this VIP:port → rewrite the destination to a real pod IP."
The kernel applies the DNAT and the packet lands on a backend pod. Same
mechanism that handles internal ClusterIP Services — the only difference is the
VIP is a routable LAN IP instead of an internal-only address.

```
  Packet from LAN hits VIP 192.168.1.200:443
          │
          ▼
  kube-proxy iptables/IPVS rule on that node:
  "dst 192.168.1.200:443 → rewrite to 10.244.1.7:443"
          │
          ▼
  Kernel DNATs destination, packet reaches backend pod
```

[Details on kube-proxy's iptables/IPVS modes →](../services/kube-proxy.md)

---

## Public internet access

MetalLB uses private IPs — unreachable from the outside. Two ways to bridge the
gap:

### Approach A: Cloudflare Tunnel (recommended)

A secure agent inside the cluster reaches _out_ to Cloudflare, building a
private tunnel. No ports opened on your router, no static IP needed.

```
  Public User
      │
      ▼  visits mysite.com
  Cloudflare DNS
      │
      ▼  routes through tunnel
  Cloudflare Agent Pod (inside cluster)
      │
      ▼  forwards to
  MetalLB VIP 192.168.1.200
```

Public DNS points to Cloudflare. Traffic arrives via the tunnel and gets handed
off to the VIP. No router config required.

### Approach B: Port forwarding (traditional)

Your home router acts as the entry gatekeeper. You tell it: "if traffic hits my
public IP on port 80/443, forward it to the MetalLB VIP inside."

```
  Public User
      │
      ▼  visits mysite.com
  Public DNS → your home WAN IP
      │
      ▼  hits router
  Home Router (port forward 80/443)
      │
      ▼  forwards to
  MetalLB VIP 192.168.1.200
```

Caveat: home IPs change. You need a DDNS script to keep your public DNS record
updated with your current WAN address.
