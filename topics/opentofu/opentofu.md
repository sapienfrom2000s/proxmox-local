# OpenTofu: The 80/20 Rule Guide

This guide focuses on the **20% of OpenTofu concepts** that will cover **80% of your daily operations** when managing infrastructure for this homelab.

---

## 🎯 The 20% Core Concepts (What You Need 80% of the Time)

To build and manage virtual machines on Proxmox, you only need to master four primary concepts:

1. **Resources & Data Sources (`resource` / `data`)**
   - **`resource`**: Declares what you want to create (e.g., "create a VM with 2GB RAM").
   - **`data`**: Queries information from existing systems without creating anything (e.g., "find the ID of the Debian 13 VM template").

2. **Variables & Outputs (`variable` / `output`)**
   - **`variable`**: Inputs to parameterize your configurations (e.g., `proxmox_api_url`, `vm_count`).
   - **`output`**: Information printed after provisioning (e.g., the IP address assigned to the new VM).

3. **State File (`terraform.tfstate`)**
   - OpenTofu's single source of truth. It is a JSON file that maps your declarative code declarations to the actual physical resources created on your Proxmox server.

4. **The Lifecycle Workflow (The 4 Commands)**
   - `tofu init`: Initializes the workspace and downloads the necessary Proxmox providers.
   - `tofu plan`: Dry-run showing exactly what will be added, changed, or destroyed.
   - `tofu apply`: Executes the changes to match the desired state.
   - `tofu destroy`: Tears down all resources managed by the configuration.

---

## 🗺️ How OpenTofu Works (ASCII Diagram)

```text
                     +---------------------------------------+
                     |  Your Desired State Code (main.tf)    |
                     +-------------------+-------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |      State File (terraform.tfstate)   |
                     |     - Current view of actual infra -  |
                     +-------------------+-------------------+
                                         |
                                         v
   +-------------------------------------+-------------------------------------+
   |                              OpenTofu Engine                              |
   |                                                                           |
   |  1. Compares code vs. state.                                              |
   |  2. Calculates diff (Create/Update/Destroy).                              |
   |  3. Sends instructions to Providers.                                      |
   +-------------------------------------+-------------------------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |       Proxmox Provider Plugin         |
                     |    - Translates tofu to API calls -   |
                     +-------------------+-------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |           Proxmox VE API              |
                     +-------------------+-------------------+
                                         |
                                         v
                     +---------------------------------------+
                     |        Debian 13 Target VMs           |
                     +---------------------------------------+
```

---

## 🧊 The 80% Advanced Stuff (Ignore Until Needed)

These are complex features that are useful in enterprise environments, but you can safely ignore them while setting up this homelab:
- **Remote State Backend & State Locking**: Essential for team environments (e.g., storing state in S3/Consul), but local storage is perfect for a single-node homelab.
- **Workspaces**: Used to manage multiple environments (dev/prod) from the same config.
- **`moved` blocks & Refactoring**: Used to rename resources in code without destroying/recreating them.
- **Dynamic Blocks**: Complex `for_each` nesting loops inside resource declarations.
- **Custom Provider Development**: Building your own API integrations.
