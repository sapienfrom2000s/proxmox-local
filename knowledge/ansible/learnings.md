# Ansible — Learnings

## 2026-07-10

### The Problem Ansible Solves

Without Ansible: SSH into each server, make changes manually, hope you didn't miss one. Config drifts, servers become snowflakes — each slightly different, nobody knows why. No audit trail, no repeatability.

Ansible solves this by letting you describe desired state in YAML, then it figures out the delta and applies it consistently across your fleet.

### Core Value Propositions

1. **Idempotency** — "Set this config" means "make sure this config exists." Run once or 100 times, same result. No duplicate entries, no "I already did that" errors.
2. **Declarative state** — Describe the desired end state, not the steps. "Package X should be installed" not "run apt install X."
3. **Inventory as truth** — Servers are a data structure, not a mental list.
4. **Auditability** — Playbooks are version-controlled YAML. Who changed what, when, why — all in git.
5. **Agentless** — Just SSH + Python on the control machine. No daemon to install, manage, or upgrade on targets.

### Mental Model

Ansible = SSH + Python modules + YAML to describe intent + idempotency engine that figures out the delta between current state and desired state.

### Core Functionalities

- **Provisioning** — install packages, create users, configure networking
- **Configuration management** — keep configs consistent across fleet
- **Orchestration** — ordered multi-host workflows (update node 1, then node 2, then node 3)
- **Ad-hoc commands** — quick one-offs without writing a playbook

### Key Concepts

- **Inventory** — list of hosts and their properties (IP, user, become settings)
- **Playbooks** — YAML files defining multi-step tasks
- **Tasks** — individual steps within a playbook
- **Modules** — built-in tools for specific things (apt, sysctl, lineinfile, etc.)
- **Ad-hoc commands** — one-off runs against hosts using `ansible` CLI

### Basic Commands

| Command | What it does |
|---|---|
| `ansible all -m ping` | Test connectivity to all hosts |
| `ansible all -m shell -a "uptime"` | Run a command on all hosts |
| `ansible-playbook site.yml` | Run a playbook |
| `ansible-playbook site.yml --limit webservers` | Run playbook on specific hosts |
| `ansible-playbook site.yml --check` | Dry run (show changes without applying) |
| `ansible-playbook site.yml --diff` | Show what changed in files |
| `ansible all -m setup` | Gather facts about all hosts |
| `ansible-doc apt` | Show documentation for a module |
| `ansible-inventory --list` | Show inventory as JSON |

### Key Modules

| Module | Does what |
|---|---|
| `command` | Runs a raw command (no shell) |
| `shell` | Runs a command through shell (pipes, redirects) |
| `apt` | Installs/removes packages |
| `sysctl` | Sets kernel params (persistent) |
| `lineinfile` | Adds/removes/changes a line in a file |
| `template` | Renders a Jinja2 template to a file |
| `copy` | Copies a file to the target |
| `service` | Starts/stops/restarts a service |

### Alternatives to Ansible

| Tool | How it differs |
|---|---|
| **Fabric** | Python code instead of YAML. Simpler, no idempotency built in. Good for scripting one-off SSH workflows. |
| **SaltStack** | Agent-based (salt-minion on targets). Faster at scale, pub/sub model. Heavier setup. |
| **Puppet** | Agent-based, Ruby DSL. Mature, strong idempotency. Steeper learning curve, more enterprise-oriented. |
| **Chef** | Agent-based, Ruby code. Powerful but complex. Better for dev teams already in Ruby ecosystem. |
| **Terraform** | Provisions infrastructure (VMs, networks, DNS). Doesn't configure what's inside. Complementary to Ansible, not a replacement. |
| **PSSH** | Just parallel SSH. No modules, no idempotency, no playbooks. Lightest weight option. |

**Bottom line**: Ansible hit the sweet spot — agentless like Fabric, declarative like Puppet, but simpler than both. For homelab/small fleet, nothing else comes close in effort-to-value ratio.

### Why is Terraform stateful but Ansible isn't?

Because they remember different things.

Ansible only needs to know which host to connect to.
Once connected, it asks the host for its current state.
The host itself is the source of truth.

Terraform needs to know which cloud resource each block in your code represents.
Cloud providers know resource IDs (i-123, vpc-456), but they don't know your Terraform names (aws_instance.web, aws_vpc.main).
Terraform must remember that mapping, so it keeps a state file.
