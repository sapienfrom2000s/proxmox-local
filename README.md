# Proxmox Local Homelab: Platform Engineering in a Box

A production-style platform engineering homelab built on a single physical HP Mini PC running **Proxmox VE**, utilizing **Debian 13** as the base OS for all virtual machines. 

The goal of this project is to model real-world cloud infrastructure patterns—such as network isolation, Infrastructure as Code (IaC), GitOps, comprehensive observability, and chaos resiliency testing—entirely on a single node, provisioned declaratively through code rather than manual UI clicks.

---

## 🚀 Key Objectives & Philosophy

- **100% Declarative & Open Source**: Everything from VM creation to application deployments is defined in code. Only open-source or free-tier tools are utilized.
- **Enterprise Network Isolation**: A split public/private subnet topology simulated via Proxmox bridges, routing all internal VM traffic through a dedicated dual-homed Gateway VM.
- **GitOps-Driven Application Delivery**: Applications and cluster configurations are continuously reconciled via ArgoCD against Git.
- **Measurable Resiliency**: Incorporating active chaos testing (e.g., hard-killing nodes under load) to measure recovery windows and validate HA configurations.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Hypervisor** | [Proxmox VE](https://www.proxmox.com/) | Bare-metal virtualization platform |
| **Base OS** | [Debian 13](https://www.debian.org/) | Light, clean Cloud-Init VM images |
| **Infrastructure as Code** | [OpenTofu](https://opentofu.org/) | Open-source fork of Terraform for VM lifecycle management |
| **Configuration Management** | [Ansible](https://www.ansible.com/) | VM post-provisioning, hardening, and package installation |
| **Secrets Management** | Ansible Vault | Safe encryption of tokens, SSH keys, and credentials |
| **Networking & Routing** | Linux Bridges, HAProxy/Nginx, CoreDNS | Public/private subnet split, reverse proxy, local `*.local` DNS |
| **Container Orchestration** | [K3s](https://k3s.io/) | Lightweight Kubernetes distribution (1x Control Plane, 2x Workers) |
| **GitOps Engine** | [ArgoCD](https://argoproj.github.io/cd/) | Continuous delivery and sync tool |
| **Observability & Telemetry**| Prometheus & Grafana | Telemetry collection, system metrics, and dashboarding |

---

## 🌐 Architecture Overview

The single-node physical architecture simulates a cloud-like Virtual Private Cloud (VPC):

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
                                       | (Public IP)
                        +--------------v--------------+
                        |         Gateway VM          |
                        |                             |
                        |   +---------------------+   |
                        |   |  iptables NAT /     |   |
                        |   |  Masquerading       |   |
                        |   +----------+----------+   |
                        |              |              |
                        |   +----------v----------+   |
                        |   | HAProxy OSS Proxy   |   |
                        |   | CoreDNS Server      |   |
                        |   +---------------------+   |
                        +--------------+--------------+
                                       | (10.0.0.1)
                               +-------v-------+
                               |     vmbr1     | (Isolated Private Bridge)
                               +-------+-------+
                                       |
                 +---------------------+---------------------+
                 | (10.0.0.10)         | (10.0.0.11)         | (10.0.0.12)
         +-------v-------+     +-------v-------+     +-------v-------+
         |    K3s CP     |     |  K3s Worker 1 |     |  K3s Worker 2 |
         | (Control Plane)     |               |     |               |
         +---------------+     +---------------+     +---------------+
  =============================================================================
```


---

## 📁 Repository Structure

```text
├── .agents/               # Agent configuration, rules, and skills
├── code/                  # All project code
│   └── iac/               # Infrastructure as Code (OpenTofu, etc.)
├── topics/                # 80/20 concept guides for each technology in the stack
├── ROADMAP.md             # The master checklist of phases and project milestones
├── WHAT_IS_DONE.md        # Detailed log of implemented configurations and decisions
├── POST_STEP_CHECKLIST.md # Conceptual validation and learning verification
└── README.md              # This file
```

---

## 🧭 Roadmap & Documentation

To see our current progress, please refer to the following documents:
- **Project Roadmap & Tasks**: Refer to [ROADMAP.md](file:///Users/thirtyone/repos/proxmox-local/ROADMAP.md) to check what phases are planned and what tasks are currently active.
- **Completed Implementations**: Review [WHAT_IS_DONE.md](file:///Users/thirtyone/repos/proxmox-local/WHAT_IS_DONE.md) for concrete details and configurations of completed tasks.
- **Topic Guides**: Browse [topics/](file:///Users/thirtyone/repos/proxmox-local/topics/) for 80/20 concept breakdowns of each technology used in this project.
