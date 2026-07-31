================================================================ HOMELAB
PLATFORM ENGINEERING ROADMAP Single-Node Proxmox VE (Debian 13) -> Multi-Node
Expansion (Future) Stack: 100% Open Source / Free-Tier Only
================================================================

PHASE 1: FOUNDATIONS & INFRASTRUCTURE AS CODE (IaC)
----------------------------------------------------------------

[x] 1.1 OpenTofu + Proxmox provider: declarative VM lifecycle (create / modify /
destroy Debian 13 Cloud-Init VMs)

[x] 1.2 Ansible post-provisioning playbooks: - SSH key-only auth, disable root
password login - kernel params (net.ipv4.ip_forward=1, etc.)

[x] 1.3 Secrets management via Doppler (cloud): - SSH keys, Proxmox API token
stored in Doppler - injected via `doppler run` -> `scripts/tofu.sh`

PHASE 2: PRODUCTION-GRADE KUBERNETES & GITOPS
------------------------------------------------

[x] 2.1 K8s cluster - 1x Server (cp), 2x Agents (alpha, beta) - See
knowledge/k8s/learnings.md for rationale

[x] 2.1b cert-manager + TLS certificates - cert-manager v1.21.0 with self-signed
CA issuer - Wildcard cert for *.home (Secret: home-tls in gateway namespace) -
Auto-renewal, CA trust via macOS Keychain + Firefox

[x] 2.2 ArgoCD (OSS) installed in-cluster - linked to a free-tier GitHub repo ->
fully declarative deploys

[x] 2.3 Gateway API (Envoy Gateway) - Installed Gateway API CRDs + Envoy Gateway
via Helm chart through ArgoCD - TLS termination for *.home on gateway
(192.168.1.203) - todo.home routed to todo-api service - Cross-namespace routing
via ReferenceGrant

PHASE 3: OBSERVABILITY
---------------------------------------------------------------

[x] 3.1 Telemetry pipeline: - Prometheus + Grafana OSS via kube-prometheus-stack
(ArgoCD app-of-apps) — node_exporter on all VMs (via DaemonSet),
CPU/memory/network dashboards - Loki (grafana-community/loki chart) for log
aggregation — monolithic mode, filesystem storage, auth disabled - Promtail
DaemonSet for log shipping to Loki

[x] 3.2 Traffic generator: - locust deployed as in-cluster pod generating
traffic against cluster workloads
