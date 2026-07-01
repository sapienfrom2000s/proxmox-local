================================================================
  HOMELAB PLATFORM ENGINEERING ROADMAP
  Single-Node Proxmox VE (Debian 13) -> Multi-Node Expansion (Future)
  Stack: 100% Open Source / Free-Tier Only
================================================================

PHASE 1: FOUNDATIONS & INFRASTRUCTURE AS CODE (IaC)
----------------------------------------------------------------
[ ] 1.1  OpenTofu + Proxmox provider: declarative VM lifecycle
         (create / modify / destroy Debian 13 Cloud-Init VMs)
      You should be able to answer:
      - What does OpenTofu state track, and why is losing it dangerous?
      - How does OpenTofu authenticate against the Proxmox API?
      - Why does running "apply" twice change nothing the second time?
      - Why OpenTofu over Terraform (license lineage, compatibility)?

[ ] 1.2  Ansible post-provisioning playbooks:
         - SSH key-only auth, disable root password login
         - kernel params (net.ipv4.ip_forward=1, etc.)
      You should be able to answer:
      - How is an Ansible inventory/role structured, and why?
      - What makes a task idempotent vs. a plain shell script?
      - Why harden SSH/kernel params before anything else touches the box?

[ ] 1.3  Secrets management via Ansible Vault:
         - encrypt SSH keys, API tokens, TLS secrets, DB creds
         - vault-id / password file kept OUT of git
      You should be able to answer:
      - What's the difference between secrets "at rest" (Vault-encrypted
        files in git) and secrets "at runtime" (injected via env/CI)?
      - If your vault password file leaked, what's compromised?
      - Why is plaintext secrets in a public repo the #1 rookie mistake?

PHASE 2: DEEP NETWORKING, ROUTING & SECURITY
----------------------------------------------------------------
[ ] 2.1  Bridge config:
         - vmbr0 -> WAN/Public (physical NIC attached)
         - vmbr1 -> Isolated internal (no physical port)
      You should be able to answer:
      - How does a Linux bridge behave like a virtual switch?
      - Why is an interface with no physical uplink still routable
        internally? How does this map to a cloud VPC?

[ ] 2.2  Gateway VM (dual-homed: vmbr0 + vmbr1):
         - IP forwarding enabled
         - iptables NAT masquerading -> acts as L3 router
      You should be able to answer:
      - What's the difference between routing and NAT?
      - How does masquerade rewrite source IPs, step by step?
      - Why is this VM a single point of failure, and what would
        break if it went down right now?

[ ] 2.3  Local DNS + TLS engine:
         - CoreDNS / Pi-hole for *.local resolution
         - HAProxy / Nginx (OSS) reverse proxy on Gateway VM
         - TLS via Let's Encrypt DNS-01 challenge
         - NOTE: requires a free-tier DNS API (e.g. Cloudflare free
           plan) for the DNS-01 TXT record automation -- the only
           non-self-hosted dependency in this stack
      You should be able to answer:
      - Why does DNS-01 work without exposing ports 80/443 to the internet?
      - How does internal service discovery differ from public DNS?
      - How does cert renewal get automated, and what happens if it fails silently?

PHASE 3: PRODUCTION-GRADE KUBERNETES & GITOPS
----------------------------------------------------------------
[ ] 3.1  K3s / kubeadm cluster inside vmbr1 (private subnet)
         - 1x Control Plane, 2x Worker nodes
      You should be able to answer:
      - What does the control plane own vs. what does the data plane own?
      - What does etcd actually store, and why does it matter?
      - Why is a single CP node a resiliency gap? (see 6.2)

[ ] 3.2  ArgoCD (OSS) installed in-cluster
         - linked to a free-tier GitHub repo -> fully declarative deploys
      You should be able to answer:
      - What is a reconciliation loop, and how does ArgoCD detect drift?
      - Why does manually running "kubectl apply" become an anti-pattern here?
      - What happens if someone edits a resource directly in the cluster?

[ ] 3.3  Ingress + Storage:
         - Traefik / Ingress-Nginx controller
         - Longhorn / OpenEBS for persistent volumes
      You should be able to answer:
      - How do ingress rules map incoming requests to services/pods?
      - How does replica placement work in distributed storage?
      - Why isn't single-host "distributed" storage actually fault-tolerant?

PHASE 4: OBSERVABILITY
----------------------------------------------------------------
[ ] 4.1  Telemetry pipeline:
         - Prometheus + Grafana OSS
         - node_exporter on all VMs (via Ansible)
         - track CPU throttling, memory pressure, iface drops
      You should be able to answer:
      - What's the difference between a pull-based and push-based
        metrics model, and which is Prometheus?
      - Can you write a basic PromQL query from memory?
      - What does your "normal" baseline look like, and how do you know?

[ ] 4.2  Load test:
         - locust / ApacheBench from external laptop -> cluster
      You should be able to answer:
      - Why do p95/p99 latency matter more than the average?
      - What does saturation look like on your dashboard before
        you introduce any failure?

PHASE 5: CHAOS RESILIENCY
----------------------------------------------------------------
[ ] 5.1  Chaos experiment:
         - scripted hard-kill of a random worker node mid-load
         - verify via Grafana: failure detected, pods rescheduled,
           dead node stripped from proxy routing
         - MEASURE (don't assume zero) request disruption window
      You should be able to answer:
      - What are node-monitor-grace-period and pod-eviction-timeout,
        and what happens if you tune them?
      - What was your actual MTTR, calculated from your own data —
        not assumed?
      - Can you walk someone through this as a postmortem: timeline,
        detection, impact, remediation, follow-up actions?

----------------------------------------------------------------
PHASE 6: FUTURE EXPANSION (post-validation, additional hardware)
----------------------------------------------------------------
[ ] 6.1  Multi-node Proxmox cluster (Corosync + shared/replicated
         storage) once hardware allows
      You should be able to answer:
      - What is quorum, and why does clustering need an odd number
        of voting members?
      - What is split-brain, and how does quorum prevent it?

[ ] 6.2  HA control plane (3-node etcd) instead of single CP node
      You should be able to answer:
      - How does etcd reach consensus (Raft), in your own words?
      - Why is control-plane HA a different problem than application HA?

[ ] 6.3  Kubernetes NetworkPolicies (Cilium/Calico OSS core) for
         pod-level isolation -- extend the isolation story past the VM layer
      You should be able to answer:
      - What is a default-deny network model, and why start there?
      - How does L3/L4 policy enforcement differ from L7 (e.g. Cilium)?

[ ] 6.4  True distributed storage fault domains across physical
         hosts (Longhorn replicas on separate machines)
      You should be able to answer:
      - What does "fault domain" actually mean once replicas sit on
        genuinely separate failure boundaries, not just separate VMs?

[ ] 6.5  Also revisit the Gateway VM SPOF from 2.2 -- consider
         keepalived/VRRP or a second gateway once you have the
         hardware for it.
      You should be able to answer:
      - How does VRRP achieve failover between two gateways?
      - What's the actual failover time, and is it acceptable?
================================================================
