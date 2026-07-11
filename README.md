# Proxmox Local Homelab: Platform Engineering in a Box

A production-style platform engineering homelab built on a single physical HP Mini PC running **Proxmox VE**, utilizing **Debian 13** as the base OS for all virtual machines. 

The goal of this project is to model real-world cloud infrastructure patterns—such as Infrastructure as Code (IaC), GitOps, comprehensive observability, and chaos resiliency testing—entirely on a single node, provisioned declaratively through code rather than manual UI clicks.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Hypervisor** | [Proxmox VE](https://www.proxmox.com/) | Bare-metal virtualization platform |
| **Base OS** | [Debian 13](https://www.debian.org/) | Light, clean Cloud-Init VM images |
| **Infrastructure as Code** | [OpenTofu](https://opentofu.org/) | Open-source fork of Terraform for VM lifecycle management |
| **Configuration Management** | [Ansible](https://www.ansible.com/) | VM post-provisioning, hardening, and package installation |
| **Secrets Management** | Ansible Vault | Safe encryption of tokens, SSH keys, and credentials |
| **Networking & Routing** | Linux Bridges, HAProxy/Nginx, CoreDNS | Reverse proxy, local `*.local` DNS |
| **Container Orchestration** | [Kubernetes](https://kubernetes.io/) | Container orchestration (1x Control Plane, 2x Workers) |
| **GitOps Engine** | [ArgoCD](https://argoproj.github.io/cd/) | Continuous delivery and sync tool |
| **Observability & Telemetry**| Prometheus & Grafana | Telemetry collection, system metrics, and dashboarding |

---

## 🌐 Architecture Overview

All VMs are attached directly to the host bridge and receive IPs from the home network:

```text
                      +-----------------------------------+
                      |        WAN / Home Network         |
                      |     [Physical Router / DHCP]      |
                      +-----------------+-----------------+
                                        |
  ============================= Host / Proxmox VE =============================
                                        |
                                +-------v-------+
                                |     vmbr0     | (Public Bridge)
                                +-------+-------+
                                        |
          +-----------------------------+-----------------------------+
          |                             |                             |
  +-------v-------+             +-------v-------+             +-------v-------+
  |    K8s CP     |             |  K8s Worker 1 |             |  K8s Worker 2 |
  | (Control      |             |               |             |               |
  |  Plane)       |             |               |             |               |
  | 192.168.1.10  |             | 192.168.1.11  |             | 192.168.1.12  |
  +---------------+             +---------------+             +---------------+
  =============================================================================
```


---

## 📁 Repository Structure

```text
├── .agents/               # Agent configuration, rules, and skills
├── code/                  # All project code
│   ├── ansible/           # Ansible playbooks and inventory
│   └── iac/               # Infrastructure as Code (OpenTofu, etc.)
├── docs/
│   ├── ROADMAP.md         # The master checklist of phases and project milestones
│   ├── WHAT_IS_DONE.md    # Detailed log of implemented configurations and decisions
│   └── POST_STEP_CHECKLIST.md # Conceptual validation and learning verification
├── knowledge/             # Personal comprehension tracking
│   └── ansible/           # Ansible learnings and examples
├── README.md              # This file
```

---

## 🧭 Roadmap & Documentation

To see our current progress, please refer to the following documents:
- **Project Roadmap & Tasks**: Refer to [ROADMAP.md](docs/ROADMAP.md) to check what phases are planned and what tasks are currently active.
- **Completed Implementations**: Review [WHAT_IS_DONE.md](docs/WHAT_IS_DONE.md) for concrete details and configurations of completed tasks.
- **Knowledge Tracking**: Browse [knowledge/](knowledge/) for personal comprehension logs of each technology used in this project.
