================================================================
  HOMELAB PLATFORM ENGINEERING ROADMAP
  Single-Node Proxmox VE (Debian 13) -> Multi-Node Expansion (Future)
  Stack: 100% Open Source / Free-Tier Only
================================================================

PHASE 1: FOUNDATIONS & INFRASTRUCTURE AS CODE (IaC)
----------------------------------------------------------------
[x] 1.1  OpenTofu + Proxmox provider: declarative VM lifecycle
          (create / modify / destroy Debian 13 Cloud-Init VMs)

[-] 1.2  Ansible post-provisioning playbooks: (skipped)
         - SSH key-only auth, disable root password login
         - kernel params (net.ipv4.ip_forward=1, etc.)

[x] 1.3  Secrets management via Doppler (cloud):
          - SSH keys, Proxmox API token stored in Doppler
          - injected via `doppler run` -> `scripts/tofu.sh`

PHASE 2: PRODUCTION-GRADE KUBERNETES & GITOPS
------------------------------------------------
[ ] 2.1  K3s cluster (chosen over kubeadm)
         - 1x Server (cp), 2x Agents (alpha, beta)
         - Embedded etcd (`--cluster-init`) chosen over default SQLite
           for crash resilience on power loss
         - See knowledge/k3s/learnings.md for rationale

[ ] 2.2  ArgoCD (OSS) installed in-cluster
         - linked to a free-tier GitHub repo -> fully declarative deploys

[ ] 2.3  Ingress + Storage:
         - Traefik / Ingress-Nginx controller
         - Longhorn / OpenEBS for persistent volumes

PHASE 3: OBSERVABILITY
----------------------------------------------------------------
[ ] 3.1  Telemetry pipeline:
         - Prometheus + Grafana OSS
         - node_exporter on all VMs (via Ansible)
         - track CPU throttling, memory pressure, iface drops

[ ] 3.2  Load test:
         - locust / ApacheBench from external laptop -> cluster

PHASE 4: CHAOS RESILIENCY
----------------------------------------------------------------
[ ] 4.1  Chaos experiment:
         - scripted hard-kill of a random worker node mid-load
         - verify via Grafana: failure detected, pods rescheduled,
           dead node stripped from proxy routing
         - MEASURE (don't assume zero) request disruption window

----------------------------------------------------------------
PHASE 5: FUTURE EXPANSION (post-validation, additional hardware)
----------------------------------------------------------------
[ ] 5.1  Multi-node Proxmox cluster (Corosync + shared/replicated
         storage) once hardware allows

[ ] 5.2  HA control plane (3-node etcd) instead of single CP node

[ ] 5.3  Kubernetes NetworkPolicies (Cilium/Calico OSS core) for
         pod-level isolation -- extend the isolation story past the VM layer

[ ] 5.4  True distributed storage fault domains across physical
         hosts (Longhorn replicas on separate machines)

[ ] 5.5  Also revisit keepalived/VRRP or a second gateway once you have the
         hardware for it.
================================================================
