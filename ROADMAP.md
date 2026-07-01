================================================================
  HOMELAB PLATFORM ENGINEERING ROADMAP
  Single-Node Proxmox VE (Debian 13) -> Multi-Node Expansion (Future)
  Stack: 100% Open Source / Free-Tier Only
================================================================

PHASE 1: FOUNDATIONS & INFRASTRUCTURE AS CODE (IaC)
----------------------------------------------------------------
[ ] 1.1  OpenTofu + Proxmox provider: declarative VM lifecycle
         (create / modify / destroy Debian 13 Cloud-Init VMs)

[ ] 1.2  Ansible post-provisioning playbooks:
         - SSH key-only auth, disable root password login
         - kernel params (net.ipv4.ip_forward=1, etc.)

[ ] 1.3  Secrets management via Ansible Vault:
         - encrypt SSH keys, API tokens, TLS secrets, DB creds
         - vault-id / password file kept OUT of git

PHASE 2: DEEP NETWORKING, ROUTING & SECURITY
----------------------------------------------------------------
[ ] 2.1  Bridge config:
         - vmbr0 -> WAN/Public (physical NIC attached)
         - vmbr1 -> Isolated internal (no physical port)

[ ] 2.2  Gateway VM (dual-homed: vmbr0 + vmbr1):
         - IP forwarding enabled
         - iptables NAT masquerading -> acts as L3 router

[ ] 2.3  Local DNS + TLS engine:
         - CoreDNS / Pi-hole for *.local resolution
         - HAProxy / Nginx (OSS) reverse proxy on Gateway VM
         - TLS via Let's Encrypt DNS-01 challenge
         - NOTE: requires a free-tier DNS API (e.g. Cloudflare free
           plan) for the DNS-01 TXT record automation -- the only
           non-self-hosted dependency in this stack

PHASE 3: PRODUCTION-GRADE KUBERNETES & GITOPS
----------------------------------------------------------------
[ ] 3.1  K3s / kubeadm cluster inside vmbr1 (private subnet)
         - 1x Control Plane, 2x Worker nodes

[ ] 3.2  ArgoCD (OSS) installed in-cluster
         - linked to a free-tier GitHub repo -> fully declarative deploys

[ ] 3.3  Ingress + Storage:
         - Traefik / Ingress-Nginx controller
         - Longhorn / OpenEBS for persistent volumes

PHASE 4: OBSERVABILITY
----------------------------------------------------------------
[ ] 4.1  Telemetry pipeline:
         - Prometheus + Grafana OSS
         - node_exporter on all VMs (via Ansible)
         - track CPU throttling, memory pressure, iface drops

[ ] 4.2  Load test:
         - locust / ApacheBench from external laptop -> cluster

PHASE 5: CHAOS RESILIENCY
----------------------------------------------------------------
[ ] 5.1  Chaos experiment:
         - scripted hard-kill of a random worker node mid-load
         - verify via Grafana: failure detected, pods rescheduled,
           dead node stripped from proxy routing
         - MEASURE (don't assume zero) request disruption window

----------------------------------------------------------------
PHASE 6: FUTURE EXPANSION (post-validation, additional hardware)
----------------------------------------------------------------
[ ] 6.1  Multi-node Proxmox cluster (Corosync + shared/replicated
         storage) once hardware allows

[ ] 6.2  HA control plane (3-node etcd) instead of single CP node

[ ] 6.3  Kubernetes NetworkPolicies (Cilium/Calico OSS core) for
         pod-level isolation -- extend the isolation story past the VM layer

[ ] 6.4  True distributed storage fault domains across physical
         hosts (Longhorn replicas on separate machines)

[ ] 6.5  Also revisit the Gateway VM SPOF from 2.2 -- consider
         keepalived/VRRP or a second gateway once you have the
         hardware for it.
================================================================
