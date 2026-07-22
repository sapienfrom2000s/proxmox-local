# Gateway API Concepts

## What is Gateway API

Gateway API is a Kubernetes standard for managing traffic ingress. It replaces
Ingress with a role-oriented model, splitting concerns between platform admins
and app developers.

```
  Platform admin                App developer
  (manages the gateway)         (manages routing)
         │                              │
         ▼                              ▼
  ┌──────────────┐              ┌───────────────┐
  │ GatewayClass │              │  HTTPRoute    │
  │   Gateway    │◄─────────────│ ReferenceGrant│
  └──────────────┘              └───────────────┘
```

## Resources

### GatewayClass

Which controller handles the traffic. One per controller type.

```
  GatewayClass
  ┌──────────────────────────────────────┐
  │ controllerName: gateway.envoyproxy   │
  │                /gatewayclass-ctrl    │
  └──────────────────────────────────────┘
           │
           │  tells Envoy Gateway
           │  "you own this"
           ▼
  ┌──────────────────────────────────────┐
  │ Envoy Gateway controller (pod)       │
  │ watches for Gateways using this      │
  │ class and provisions Envoy proxies   │
  └──────────────────────────────────────┘
```

### Gateway

The entry point: port, hostname pattern, TLS certificate.

```
  Gateway (home-gateway)
  ┌──────────────────────────────────────────┐
  │ className: envoy-gateway                 │
  │ listener:                                │
  │   port: 443                              │
  │   hostname: "*.home"                     │
  │   TLS Terminate using Secret: home-tls   │
  └──────────────────────────────────────────┘
```

Creating this makes Envoy Gateway spin up an Envoy proxy pod and expose it as a
LoadBalancer Service with a MetalLB IP.

### HTTPRoute

Routing rules: which hostname maps to which backend service.

```
  HTTPRoute (todo-api)
  ┌──────────────────────────────────────────┐
  │ parentRef: home-gateway                  │
  │ hostname: "todo.home"                    │
  │ backendRef:                              │
  │   name: todo-api                         │
  │   namespace: todo                        │
  │   port: 80                               │
  └──────────────────────────────────────────┘
```

Multiple HTTPRoutes attach to the same Gateway, each handling a different
hostname or path.

### ReferenceGrant

Required when an HTTPRoute references a service in a different namespace.
Without it, the gateway controller blocks the cross-namespace reference.

```
  HTTPRoute (gateway ns) ──references──► Service (todo ns)
                     │                       │
                     │   ReferenceGrant      │
                     └───── allows this ─────┘
                        (lives in todo ns)
```

---

## DNS

dnsmasq on the Proxmox host (192.168.1.9) resolves `*.home` addresses:

```
  /etc/dnsmasq.d/k8s.conf
  ┌──────────────────────────────────────────────┐
  │ address=/nginx.home/192.168.1.200            │
  │ address=/argocd.home/192.168.1.201           │
  │ address=/todo.home/192.168.1.203             │
  └──────────────────────────────────────────────┘
```

All `*.home` hostnames must point to the gateway IP (192.168.1.203), not the
service's own LoadBalancer IP. Traffic must enter through the gateway for TLS
termination and routing to work.

---

## Troubleshooting

**Browser certificate error:**

- Root CA not trusted — import into Keychain or Firefox cert store
- Hostname not in SANs — add explicit entry to certificate.yaml
- Verify: `openssl s_client -connect IP:443 -servername hostname`

**503 or no route:**

- `kubectl get httproute -A` — route exists?
- `kubectl get gateway -n gateway` — PROGRAMMED true?
- ReferenceGrant exists if backend is cross-namespace

**Connection refused:**

- `kubectl get svc -A | grep envoy` — external IP assigned?
- DNS resolves to gateway IP, not service IP
