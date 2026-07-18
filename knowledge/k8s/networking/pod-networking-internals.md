# Pod Networking Internals

```
                        ┌──────────┐
                        │ Internet │
                        └────┬─────┘
                             │
                    ┌────────┴────────┐
                    │   NIC (eth0)    │
                    │ 192.168.1.x     │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  │      iptables       │
                  └──────────┬──────────┘
                             │
               ┌─────────────┴─────────────┐
               │    Linux Bridge (cni0)    │
               └──┬──────────┬──────────┬──┘
                  │          │          │
             [veth-a]   [veth-b]   [veth-c]
               ┌────┐    ┌────┐    ┌────┐
               │Pod │    │Pod │    │Pod │
               │ A  │    │ B  │    │ C  │
               └────┘    └────┘    └────┘
```

### veth (Virtual Ethernet)

A veth is a virtual cable with two ends. What goes in one end comes out the other — nothing more. No switching, no learning. It exists solely to connect two isolated network namespaces. In k8s, every pod gets its own network namespace, and a veth pair is what plugs that namespace into the node's network.

### Linux Bridge

A software switch inside the kernel. It connects multiple interfaces and forwards frames between them based on MAC addresses — exactly like a physical network switch, just running in software. Every node runs one, and all the pod veths on that node plug into it. Two pods on the same node exchange traffic through the bridge without ever touching the NIC.

### Why pods don't talk to each other directly

Pods are ephemeral. Deployments roll out new pods, crashes trigger restarts, autoscaling adds and removes them. Every time a pod is recreated, it gets a new IP. Hardcoding pod IPs is fragile — a single restart breaks every caller.

So instead, pods talk through **Services**. A Service gives a stable virtual IP (ClusterIP) and load-balances across healthy pods behind it. The actual pods can come and go; the ClusterIP never changes. This is what DNS resolves to inside the cluster — `my-service.default.svc.cluster.local` → ClusterIP, not a pod IP.

Which brings us back to the problem: if the bridge bypasses iptables, kube-proxy's rules that map ClusterIP → real pod IP never fire. The Service abstraction layer — the thing pods actually rely on to find each other — breaks completely.

### iptables

The Linux kernel's packet filtering and NAT framework. Every packet traversing the network stack passes through iptables, which applies a series of rules in order. Rules can accept, drop, reject, or rewrite packets.

In k8s, iptables does three things:

1. **Service load balancing (kube-proxy):** When a pod talks to a ClusterIP, kube-proxy has programmed iptables rules that rewrite the destination to a real pod IP, distributing traffic across endpoints. Without this, ClusterIPs don't work.

2. **Network policies:** Kubernetes NetworkPolicy objects are translated into iptables allow/deny rules that control which pods can talk to which.

3. **NAT for egress:** Pod IPs are private (e.g., 10.244.0.0/16). When a pod sends traffic to the internet, iptables masquerades it — rewrites the source IP to the node's public-facing IP so the reply can find its way back.

### DNAT

DNAT (Destination NAT) is how Services actually work. A packet arrives at the bridge with destination IP = ClusterIP (a virtual IP that no pod actually owns). iptables swaps the destination header to a real pod IP. The receiving pod never knew a ClusterIP existed — it just sees traffic arriving at its own IP. The reverse happens on the way back, so the calling pod thinks it talked to the ClusterIP the whole time.

### br_netfilter

By default, a Linux bridge operates at L2 — it switches Ethernet frames. Traffic forwarded by the bridge **bypasses iptables entirely**. This is fine for normal bridging, but it breaks k8s.

`br_netfilter` fixes this by forcing the bridge to pass packets through iptables. Combined with IP forwarding, it turns the bridge from a dumb L2 switch into a routing-aware gateway where iptables can inspect, filter, and rewrite traffic — which is exactly what kube-proxy and network policies depend on.

**The chain:** Pods are ephemeral → they talk through Services → Services need iptables → iptables needs br_netfilter to see bridge traffic.
