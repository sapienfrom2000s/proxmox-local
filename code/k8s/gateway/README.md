# Gateway API with Envoy Gateway

TLS termination and hostname-based routing for all homelab services.

## Request flow

```
  Browser: https://todo.home
       │
       ▼
  DNS (dnsmasq on .9)
       │  resolves todo.home → 192.168.1.203
       ▼
  MetalLB (LoadBalancer IP: 192.168.1.203)
       │
       ▼
  Envoy Proxy pod
       │  1. TLS handshake using home-tls cert
       │  2. client verifies cert against home-ca (root CA)
       │  3. reads hostname from SNI: "todo.home"
       │  4. matches HTTPRoute for "todo.home"
       │  5. checks ReferenceGrant (cross-namespace OK)
       │  6. forwards to todo-api.todo:80
       ▼
  ┌────────────────────┐
  │ todo-api (todo ns) │
  └────────────────────┘
```

For detailed explanations, see:

- [docs/gateway.md](docs/gateway.md) — Gateway API resources, DNS,
  troubleshooting
- [docs/certificates.md](docs/certificates.md) — certificates, trust chain,
  signatures

## Installation

### 1. Gateway API CRDs

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml
```

### 2. Envoy Gateway

Via Helm:

```bash
helm repo add envoy-gateway oci://docker.io/envoyproxy/gateway-helm
helm install eg envoy-gateway/gateway-helm \
  -n envoy-gateway-system --create-namespace
```

Via ArgoCD: Helm source type, repo `oci://docker.io/envoyproxy/gateway-helm`,
chart `gateway-helm`, version `v1.8.3`.(we did this)

### 3. Gateway resources

```bash
kubectl apply -f gateway/gatewayclass.yaml
kubectl apply -f gateway/namespace.yaml
kubectl apply -f gateway/certificate.yaml
kubectl apply -f gateway/gateway.yaml
kubectl apply -f gateway/reference-grant-todo.yaml
kubectl apply -f gateway/todo-home.yaml
```

## Adding a new service

1. Update dnsmasq on .9: `address=/myservice.home/192.168.1.203`
2. Restart dnsmasq
3. Add hostname to `certificate.yaml` dnsNames list
4. Re-apply the certificate
5. Create an HTTPRoute in the `gateway` namespace
6. If backend is in a different namespace, create a ReferenceGrant

## Files

```
code/k8s/gateway/
├── README.md                 # This file
├── docs/
│   ├── gateway.md            # Gateway API concepts
│   └── certificates.md       # Certificate concepts
├── gatewayclass.yaml         # GatewayClass
├── namespace.yaml            # Gateway namespace
├── certificate.yaml          # Wildcard cert for *.home
├── gateway.yaml              # Gateway listener
├── reference-grant-todo.yaml # Cross-namespace routing permission
└── todo-home.yaml            # HTTPRoute for todo.home
```
