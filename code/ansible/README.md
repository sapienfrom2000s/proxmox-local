# Ansible

Post-provisioning configuration management for the homelab VMs.

## Structure

```
ansible/
├── ansible.cfg        # Ansible configuration (inventory path, defaults)
├── inventory.ini      # Host definitions and variables
├── playbooks/
│   └── site.yml       # Main playbook entry point
└── README.md          # This file
```

## Quick Start

```bash
# Test connectivity to all hosts
ansible all -m ping

# Run the main playbook
ansible-playbook playbooks/site.yml

# Run on specific group
ansible-playbook playbooks/site.yml --limit workers

# Dry run (check mode)
ansible-playbook playbooks/site.yml --check
```

## Inventory

| Host | IP | Role |
|------|-----|------|
| cp | 192.168.1.10 | K8s Control Plane |
| alpha | 192.168.1.11 | K8s Worker |
| beta | 192.168.1.12 | K8s Worker |

## Variables

Set in `inventory.ini` under `[all:vars]`:

- `ansible_user=debian` — SSH user (matches Cloud-Init config)
- `ansible_become=yes` — Use sudo for all tasks
- `ansible_ssh_common_args` — Skip host key verification for fresh VMs
