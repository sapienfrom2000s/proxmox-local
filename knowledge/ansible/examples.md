# Ansible — Examples

## Inventory (`inventory.ini`)

```ini
[webservers]
web1 ansible_host=192.168.1.10
web2 ansible_host=192.168.1.11

[dbservers]
db1 ansible_host=192.168.1.20 ansible_user=admin

[all:vars]
ansible_user=ubuntu
ansible_become=yes
```

## Playbook (`site.yml`)

```yaml
---
- name: Configure web servers
  hosts: webservers
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Start nginx
      service:
        name: nginx
        state: started
```

## Task (from above)

Each `- name:` block in a playbook is a task:

```yaml
    - name: Install nginx
      apt:
        name: nginx
        state: present
```

## Module

```yaml
    - name: Ensure config line exists
      lineinfile:
        path: /etc/nginx/nginx.conf
        line: "worker_processes auto;"
        state: present
```

## Ad-hoc Commands

```bash
# Ping all hosts
ansible all -m ping

# Run a command on webservers
ansible webservers -m shell -a "systemctl status nginx"

# Install a package on dbservers
ansible dbservers -m apt -a "name=postgresql state=present" --become
```
