# Ansible

Post-provisioning configuration management for the homelab VMs.

## Structure

```
ansible/
├── ansible.cfg        # Ansible configuration (inventory path, defaults)
├── docs/
│   ├── ANSIBLE_CFG.md       # ansible.cfg explanation
│   └── MODULES_AND_COMMANDS.md  # Modules vs commands, -m flag, ping module
├── inventory.ini      # Host definitions and variables
├── requirements.txt   # Pinned Ansible version
├── playbooks/
│   ├── site.yml             # Post-provisioning setup (connectivity test)
│   └── k8s/
│       ├── prerequisites.yml    # Swap, kernel modules, containerd, k8s packages
│       ├── control-plane.yml    # kubeadm init, Calico CNI, join command
│       └── workers.yml          # kubeadm join
└── README.md          # This file
```

## Quick Start

```bash
# Install pinned Ansible version
pip install -r requirements.txt

# Test connectivity to all hosts
ansible all -m ping

# Run post-provisioning setup
ansible-playbook playbooks/site.yml

# Set up the K8s cluster
ansible-playbook playbooks/k8s/prerequisites.yml
ansible-playbook playbooks/k8s/control-plane.yml
ansible-playbook playbooks/k8s/workers.yml

# Or run all k8s playbooks in sequence
ansible-playbook playbooks/k8s/prerequisites.yml && ansible-playbook playbooks/k8s/control-plane.yml && ansible-playbook playbooks/k8s/workers.yml
```

## Inventory

| Host  | IP           | Role              |
| ----- | ------------ | ----------------- |
| cp    | 192.168.1.10 | K8s Control Plane |
| alpha | 192.168.1.11 | K8s Worker        |
| beta  | 192.168.1.12 | K8s Worker        |

## Variables

Set in `inventory.ini` under `[all:vars]`:

- `ansible_user=debian` — SSH user (matches Cloud-Init config)
- `ansible_become=yes` — Use sudo for all tasks
- `ansible_ssh_common_args` — Skip host key verification for fresh VMs

## What the Playbooks Do

1. **prerequisites.yml** (all nodes): Disables swap, loads kernel modules,
   configures sysctl, installs containerd and Kubernetes packages
2. **control-plane.yml** (cp): Runs `kubeadm init`, installs Calico CNI,
   generates join command
3. **workers.yml** (alpha, beta): Fetches join command from cp, runs
   `kubeadm join`

All playbooks are idempotent — safe to re-run if a step fails.

Run individually:

```bash
ansible-playbook playbooks/k8s/prerequisites.yml
ansible-playbook playbooks/k8s/control-plane.yml
ansible-playbook playbooks/k8s/workers.yml
```

## Configuration

See [docs/ANSIBLE_CFG.md](docs/ANSIBLE_CFG.md) for detailed explanation of
`ansible.cfg`.
