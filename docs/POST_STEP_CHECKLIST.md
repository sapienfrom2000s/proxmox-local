# Post-Step Checklist: Architectural & Conceptual Validation

> [!NOTE]
> This file is ignored by the agent. It is intended for manual validation by the user.

This checklist contains the validation questions for each step of the Homelab Platform Engineering project. Use these to verify conceptual understanding and validate architectural decisions.

---

## Phase 1: Foundations & Infrastructure as Code (IaC)

### 1.1 OpenTofu + Proxmox provider
- What does OpenTofu state track, and why is losing it dangerous?
- How does OpenTofu authenticate against the Proxmox API?
- Why does running "apply" twice change nothing the second time?
- Why OpenTofu over Terraform (license lineage, compatibility)?

### 1.2 Ansible post-provisioning playbooks
- How is an Ansible inventory/role structured, and why?
- What makes a task idempotent vs. a plain shell script?
- Why harden SSH/kernel params before anything else touches the box?

### 1.3 Secrets management via Ansible Vault
- What's the difference between secrets "at rest" (Vault-encrypted files in git) and secrets "at runtime" (injected via env/CI)?
- If your vault password file leaked, what's compromised?
- Why is plaintext secrets in a public repo the #1 rookie mistake?

---

## Phase 2: Deep Networking, Routing & Security

### 2.1 Bridge config
- How does a Linux bridge behave like a virtual switch?
- Why is an interface with no physical uplink still routable internally? How does this map to a cloud VPC?

### 2.2 Gateway VM
- What's the difference between routing and NAT?
- How does masquerade rewrite source IPs, step by step?
- Why is this VM a single point of failure, and what would break if it went down right now?

### 2.3 Local DNS + TLS engine
- Why does DNS-01 work without exposing ports 80/443 to the internet?
- How does internal service discovery differ from public DNS?
- How does cert renewal get automated, and what happens if it fails silently?

---

## Phase 3: Production-Grade Kubernetes & GitOps

### 3.1 K8s cluster
- What does the control plane own vs. what does the data plane own?
- What does etcd actually store, and why does it matter?
- Why is a single CP node a resiliency gap? (see 6.2)

### 3.2 ArgoCD
- What is a reconciliation loop, and how does ArgoCD detect drift?
- Why does manually running "kubectl apply" become an anti-pattern here?
- What happens if someone edits a resource directly in the cluster?

### 3.3 Ingress + Storage
- How do ingress rules map incoming requests to services/pods?
- How does replica placement work in distributed storage?
- Why isn't single-host "distributed" storage actually fault-tolerant?

---

## Phase 4: Observability

### 4.1 Telemetry pipeline
- What's the difference between a pull-based and push-based metrics model, and which is Prometheus?
- Can you write a basic PromQL query from memory?
- What does your "normal" baseline look like, and how do you know?

### 4.2 Load test
- Why do p95/p99 latency matter more than the average?
- What does saturation look like on your dashboard before you introduce any failure?

---

## Phase 5: Chaos Resiliency

### 5.1 Chaos experiment
- What are node-monitor-grace-period and pod-eviction-timeout, and what happens if you tune them?
- What was your actual MTTR, calculated from your own data — not assumed?
- Can you walk someone through this as a postmortem: timeline, detection, impact, remediation, follow-up actions?

---

## Phase 6: Future Expansion

### 6.1 Multi-node Proxmox cluster
- What is quorum, and why does clustering need an odd number of voting members?
- What is split-brain, and how does quorum prevent it?

### 6.2 HA control plane (3-node etcd)
- How does etcd reach consensus (Raft), in your own words?
- Why is control-plane HA a different problem than application HA?

### 6.3 Kubernetes NetworkPolicies (Cilium/Calico OSS core)
- What is a default-deny network model, and why start there?
- How does L3/L4 policy enforcement differ from L7 (e.g. Cilium)?

### 6.4 True distributed storage fault domains
- What does "fault domain" actually mean once replicas sit on genuinely separate failure boundaries, not just separate VMs?

### 6.5 Gateway VM SPOF
- How does VRRP achieve failover between two gateways?
- What's the actual failover time, and is it acceptable?
