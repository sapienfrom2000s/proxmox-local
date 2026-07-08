# Completed Milestones & Implementations

This document logs detailed notes on the implementation details, configurations, and actions taken for each completed phase and milestone in the homelab.

---

## Phase 1: Foundations & Infrastructure as Code (IaC)

### 1.1 — OpenTofu + Proxmox provider: declarative VM lifecycle

- Created `tofu@pve` service user with scoped API token and custom role on Proxmox host
- Downloaded Debian 13 cloud image and created VM template 9000
- Scaffolded OpenTofu project: `versions.tf`, `providers.tf`, `variables.tf`, `terraform.tfvars.example`, `main.tf`, `outputs.tf`
- 3 VMs defined via `for_each` (cp, alpha, beta) with Cloud-Init networking and SSH key injection
- Template setup documented step-by-step in `code/iac/README.md`
- Chose `bpg/proxmox` provider for active maintenance and native Cloud-Init support
- State committed to git for single-operator durability

### 1.2 — Ansible post-provisioning playbooks

Deliberately skipped.

### 1.3 — Secrets management via Doppler

- Installed Doppler CLI (`brew install dopplerhq/cli/doppler`)
- Created project `proxmox-local` with `dev` config
- Stored secrets: `PROXMOX_ENDPOINT`, `PROXMOX_API_TOKEN`, `SSH_PUBLIC_KEY`, `SSH_PRIVATE_KEY`
- Created `scripts/tofu.sh` wrapper that maps Doppler secrets to `TF_VAR_*` env vars for OpenTofu
- Removed sensitive values from `terraform.tfvars` (kept only non-sensitive config)
- Workflow: `doppler run -- bash scripts/tofu.sh plan|apply`
- Sensitive values no longer exist on disk unencrypted
