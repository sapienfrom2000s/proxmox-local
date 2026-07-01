# Project Rules & Workspace Context

## Project Goal
Building a production-style platform engineering homelab on a **single physical HP Mini PC** running **Proxmox VE**, with **Debian 13** as the base OS for all VMs.

The goal is to simulate real cloud infrastructure patterns — network isolation (public/private subnet split), Infrastructure as Code, GitOps, observability, and chaos resiliency testing — entirely on this one box, provisioned through code rather than manual UI clicks.

This starts as a single-node build. More physical nodes may be added later once this setup is validated. See [ROADMAP.md](file:///Users/thirtyone/repos/k8s-journey/ROADMAP.md) for the detailed phase-by-phase checklist and current progress.

## Operational Constraints
- Ensure all solutions utilize 100% open-source or free-tier tools.
- Implement configurations using Infrastructure as Code (OpenTofu, Ansible, Kubernetes YAML, Helm) as defined in the roadmap.
- Every architectural choice should be able to answer the corresponding theoretical and practical validation questions listed in [ROADMAP.md](file:///Users/thirtyone/repos/k8s-journey/ROADMAP.md).
