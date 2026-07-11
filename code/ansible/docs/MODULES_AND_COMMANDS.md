# Modules vs Commands

**Module** — Built-in, idempotent, state-aware. Checks current state, applies only delta.

```bash
ansible all -m apt -a "name=git state=present"  # does nothing if already installed
```

**Command** — Raw execution. No idempotency.

```bash
ansible all -m command -a "apt install git"  # runs every time
```

## The `-m` Flag

Specifies which module to run. Without it, Ansible uses `command`.

## Ping Module

`ansible all -m ping` is NOT ICMP. It:

1. SSHs into the host
2. Verifies Python, credentials, sudo
3. Returns `pong`

```bash
ansible all -m ping         # Can Ansible manage this host?
ansible all -m command -a "ping -c 1 192.168.1.10"  # Can I reach this IP?
```
