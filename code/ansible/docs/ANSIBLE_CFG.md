# ansible.cfg

Ansible's config file — sets defaults so you don't pass flags every time. Automatically read from the current directory and applied to every command.

```ini
[defaults]
inventory = inventory.ini
remote_user = debian
host_key_checking = False
retry_files_enabled = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False
```

## [defaults] — General behavior

| Setting | What it does |
|---|---|
| `inventory = inventory.ini` | Where to find hosts (instead of `/etc/ansible/hosts`) |
| `remote_user = debian` | SSH user for all connections |
| `host_key_checking = False` | Skip SSH fingerprint prompts |
| `retry_files_enabled = False` | Don't create `.retry` files on failure |

Without this section:
```bash
ansible all -m ping -i inventory.ini -u debian -o StrictHostKeyChecking=no
```

## [privilege_escalation] — Sudo configuration

| Setting | What it does |
|---|---|
| `become = True` | Always use sudo |
| `become_method = sudo` | Escalation tool |
| `become_user = root` | Escalate to root |
| `become_ask_pass = False` | Don't prompt for sudo password |

Without this section:
```bash
ansible all -m ping --become --ask-become-pass
```

## Without ansible.cfg

```bash
ansible-playbook playbooks/site.yml -i inventory.ini -u debian --become --ask-become-pass -o StrictHostKeyChecking=no
```

## With ansible.cfg

```bash
ansible-playbook playbooks/site.yml
```
