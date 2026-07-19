# MetalLB

Bare-metal load balancer for Kubernetes. When a Service uses
`type: LoadBalancer`, cloud providers assign an external IP. On bare-metal, that
never happens — MetalLB fills the gap.

## How it works

1. Watches for Services of type `LoadBalancer`
2. Picks an IP from the configured IPAddressPool (`192.168.1.200-192.168.1.250`)
3. Announces it on the LAN so your network can reach it
4. Sets `status.loadBalancer.ingress[0].ip` on the Service

No annotations needed — any LoadBalancer service gets an IP automatically.

## Installation

```bash
# 1. Install MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml

# 2. Apply IP pool + L2 advertisement
kubectl apply -f code/k8s/metallb/config.yml
```

## Components

- **Controller** (Deployment) — manages IP allocation
- **Speaker** (DaemonSet) — one per node, announces IPs on the network

## Files

```
code/k8s/metallb/
├── install.yml    # Official manifest reference
└── config.yml     # IPAddressPool + L2Advertisement
```
