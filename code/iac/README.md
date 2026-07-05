# Infrastructure as Code

OpenTofu configurations for provisioning VMs on Proxmox VE.

---

## VM Specifications

All VMs run **Debian 13 (Trixie)** and use **local-lvm** storage (Proxmox default).

| VM Name | Role          | RAM   | Disk  |
|---------|---------------|-------|-------|
| `cp`    | Control Plane | 2 GB  | 20 GB |
| `alpha` | Worker Node   | 3 GB  | 30 GB |
| `beta`  | Worker Node   | 3 GB  | 30 GB |

---

## Pipeline: From Bare Proxmox to Running VMs

The full provisioning pipeline has two stages: **manual one-time setup** on the Proxmox host, then **declarative IaC** via OpenTofu.

### Stage 1: Proxmox Host Preparation (One-Time, Manual)

These steps are performed directly on the Proxmox host via SSH or the web shell. They only need to be done once.

#### 1.1 Create an API Token for OpenTofu

OpenTofu talks to Proxmox through its REST API. Instead of using root credentials, we create a dedicated API token.

```bash
# Create a role with the minimum permissions OpenTofu needs
pveum role add TofuRole -privs "VM.Allocate VM.Clone VM.Config.CDROM VM.Config.CPU VM.Config.Cloudinit VM.Config.Disk VM.Config.HWType VM.Config.Memory VM.Config.Network VM.Config.Options VM.Audit VM.Monitor VM.PowerMgmt Datastore.AllocateSpace Datastore.Audit SDN.Use"

# Create a dedicated user
pveum user add tofu@pve

# Assign the role to the user
pveum aclmod / -user tofu@pve -role TofuRole

# Generate an API token (save the output — the secret is shown only once)
pveum user token add tofu@pve tofu-token --privsep 0
```

> **Save the token ID and secret.** Format will be: `tofu@pve!tofu-token` and a UUID secret. These go into your OpenTofu variables (never committed to git).

#### 1.2 Download the Debian 13 Cloud Image

Cloud images are pre-built, minimal OS images designed for automated provisioning via Cloud-Init. They skip the manual installer entirely.

```bash
# Download the Debian 13 (Trixie) cloud image to the Proxmox host
wget -P /tmp https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2
```

#### 1.3 Install Required Packages in the Cloud Image

The Debian cloud image is minimal. Install `qemu-guest-agent` so Proxmox can report accurate resource usage and IPs from cloned VMs.

```bash
# Install libguestfs-tools (if not already present)
apt-get update && apt-get install -y libguestfs-tools

# Customize the cloud image offline (no VM boot required)
virt-customize -a /tmp/debian-13-generic-amd64.qcow2 \
  --install qemu-guest-agent
```

> `virt-customize` modifies the `.qcow2` file in-place before it's imported into Proxmox. Every VM cloned from the template will already have `qemu-guest-agent` installed and ready.

#### 1.4 Create a VM Template from the Cloud Image

A **template** is a frozen, read-only VM that acts as a stamp. OpenTofu clones this template to create each new VM, instead of installing Debian from scratch every time.

```bash
# Allocates a new VM with ID 9000, names it debian-13-cloud, gives it 2GB RAM,
# and attaches a single virtio NIC to bridge vmbr0. No disk yet — just a shell.
qm create 9000 --name debian-13-cloud --memory 2048 --net0 virtio,bridge=vmbr0

# Takes the downloaded cloud image (.qcow2) and copies it into Proxmox's
# local-lvm storage as a raw disk volume attached to VM 9000. Creates
# a volume like vm-9000-disk-0.
qm importdisk 9000 /tmp/debian-13-generic-amd64.qcow2 local-lvm

# Attaches the imported disk as the VM's primary SCSI drive (scsi0) using
# the virtio-SCSI controller — better performance than IDE/SATA.
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0

# Adds a small Cloud-Init drive on ide2 (a CD-ROM-like device). On first
# boot, the VM reads Cloud-Init config (hostname, SSH key, network) from
# this drive and applies it.
qm set 9000 --ide2 local-lvm:cloudinit

# Sets boot order: 'c' = first HDD (the SCSI disk). --bootdisk scsi0
# explicitly marks which disk is the boot device.
qm set 9000 --boot c --bootdisk scsi0

# Enables a serial console (serial0) and routes VGA output through it.
# Cloud-Init uses the serial console to report status — without this,
# you can't tell if Cloud-Init succeeded on first boot.
qm set 9000 --serial0 socket --vga serial0

# Freezes VM 9000 into a read-only template. After this, the VM cannot
# be started or modified — it can only be cloned. This is the stamp
# that OpenTofu clones 3 times to create cp, alpha, and beta.
qm template 9000
```

After this, VM ID `9000` is a **template** — it cannot be started or modified, only cloned.

---

### Stage 2: OpenTofu Provisioning (Declarative, Repeatable)

With the template ready, OpenTofu handles everything from here. It clones the template 3 times, applies the per-VM specs (RAM, disk, name), injects Cloud-Init config (SSH keys, network), and powers on the VMs.

```text
  Cloud Image (.qcow2)
        |
        v
  +---------------------+
  | VM Template (9000)   |   <-- Created once in Stage 1
  +---------------------+
        |
        +--- clone ---> cp    (2 GB RAM, 20 GB disk)
        |
        +--- clone ---> alpha (3 GB RAM, 30 GB disk)
        |
        +--- clone ---> beta  (3 GB RAM, 30 GB disk)
```

#### What OpenTofu Does Per VM

1. **Clone** the template → creates a full, independent VM
2. **Resize the disk** → expands from the template's base size to the target (20 or 30 GB)
3. **Set hardware** → configures RAM, CPU cores
4. **Inject Cloud-Init config** → sets hostname, SSH public key, network (static IP or DHCP)
5. **Start the VM** → first boot runs Cloud-Init, which applies the injected config

#### What Cloud-Init Does on First Boot

Cloud-Init runs exactly once, on the first boot of each cloned VM:

1. Sets the **hostname** (e.g., `cp`, `alpha`, `beta`)
2. Injects the **SSH public key** into the default user
3. Configures **networking** (IP address, gateway, DNS)
4. Grows the **filesystem** to fill the resized disk
5. Signals **ready** via the serial console
