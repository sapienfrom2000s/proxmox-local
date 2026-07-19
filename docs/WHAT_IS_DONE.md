# Completed Milestones & Implementations

This document logs detailed notes on the implementation details, configurations,
and actions taken for each completed phase and milestone in the homelab.

---

## Phase 1: Foundations & Infrastructure as Code (IaC)

### 1.1 — OpenTofu + Proxmox provider: declarative VM lifecycle

- Created `tofu@pve` service user with scoped API token and custom role on
  Proxmox host
- Downloaded Debian 13 cloud image and created VM template 9000
- Scaffolded OpenTofu project: `versions.tf`, `providers.tf`, `variables.tf`,
  `terraform.tfvars.example`, `main.tf`, `outputs.tf`
- 3 VMs defined via `for_each` (cp, alpha, beta) with Cloud-Init networking and
  SSH key injection
- Template setup documented step-by-step in `code/iac/README.md`
- Chose `bpg/proxmox` provider for active maintenance and native Cloud-Init
  support
- State committed to git for single-operator durability

### 1.2 — Ansible post-provisioning playbooks

Deliberately skipped.

### 1.3 — Secrets management via Doppler

- Installed Doppler CLI (`brew install dopplerhq/cli/doppler`)
- Created project `proxmox-local` with `dev` config
- Stored secrets: `TF_VAR_PROXMOX_ENDPOINT`, `TF_VAR_API_TOKEN`,
  `TF_VAR_SSH_PUBLIC_KEY`
- Renamed Tofu variables to UPPER_CASE so `TF_VAR_*` names match directly (no
  wrapper needed)
- Removed sensitive values from `terraform.tfvars` (kept only non-sensitive
  config)
- Workflow: `doppler run -- tofu plan|apply`
- Sensitive values no longer exist on disk unencrypted

---

## Phase 2: Kubernetes Cluster Setup

### 2.1 — Ansible playbooks for kubeadm

- Created modular playbooks in `code/ansible/playbooks/k8s/`:
  - `prerequisites.yml`: swap, kernel modules, sysctl, containerd,
    kubeadm/kubelet/kubectl
  - `control-plane.yml`: kubeadm init, Calico CNI, join command generation
  - `workers.yml`: kubeadm join via fetched token
- Updated inventory with k8s-compatible group names (`kube_control_plane`,
  `kube_node`)
- Pinned `ansible-core==2.21.1` in `requirements.txt`
- Fixed Debian trixie compatibility: replaced deprecated `apt-key` with
  `/etc/apt/keyrings/` + `signed-by`
- Enabled CRI plugin in containerd config (disabled by default in Docker's
  package)
- All playbooks are idempotent — safe to re-run
- 3-node cluster running: cp (192.168.1.10), alpha (192.168.1.11), beta
  (192.168.1.12)
- Kubernetes v1.36.2, Calico CNI, all nodes Ready

### 2.2 — MetalLB (bare-metal LoadBalancer)

- Installed MetalLB v0.14.9 via official manifest
- IPAddressPool: `192.168.1.200-192.168.1.250`
- L2Advertisement: announces IPs on the LAN via ARP
- Watches for Services of type `LoadBalancer` — no annotations needed
- Config stored in `code/k8s/metallb/`

### 2.3 — dnsmasq (local DNS)

- Installed dnsmasq on Proxmox host (192.168.1.9) via Ansible
- Resolves `*.home` entries to K8s service IPs
- Example: `nginx.home → 192.168.1.200` (MetalLB-assigned IP)
- Config in `/etc/dnsmasq.d/k8s.conf` on the Proxmox host
- Used `.home` TLD instead of `.local` (`.local` is reserved for mDNS/Bonjour on
  macOS)
