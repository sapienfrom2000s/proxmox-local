# K8s Playbooks

Ansible playbooks for setting up a Kubernetes cluster via kubeadm.

## Playbooks

| Playbook          | Runs on            | What it does                                                                                        |
| ----------------- | ------------------ | --------------------------------------------------------------------------------------------------- |
| prerequisites.yml | all nodes          | Disables swap, loads kernel modules, configures sysctl, installs containerd and Kubernetes packages |
| control-plane.yml | kube_control_plane | Runs `kubeadm init`, installs Calico CNI, generates join command                                    |
| workers.yml       | kube_node          | Fetches join command from control plane, runs `kubeadm join`                                        |

## Usage

Run in order:

```bash
ansible-playbook playbooks/k8s/prerequisites.yml
ansible-playbook playbooks/k8s/control-plane.yml
ansible-playbook playbooks/k8s/workers.yml
```

## Idempotency

All playbooks are idempotent. Safe to re-run if a step fails — completed steps
are skipped.

## Variables

Defined in `prerequisites.yml`:

- `kubernetes_version: "1.36"` — Kubernetes version to install

Defined in `control-plane.yml`:

- `pod_network_cidr: "10.244.0.0/16"` — Pod network CIDR (used by Calico)
- `service_cidr: "10.96.0.0/12"` — Service CIDR
