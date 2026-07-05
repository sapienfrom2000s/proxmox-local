# Proxmox — Learnings

## 2026-07-05

### VM Templates

A template is a locked, reusable "master" VM you clone from instead of installing an OS every time. Clones can be full (independent copy) or linked (space-efficient, but tied to the template's continued existence).

### The Big Picture: Building a Cloud-Init Template

There's a logical progression of decisions, each solving a distinct problem:

1. **Identity & resources** — give the VM a unique ID, name, memory, and network connection. At this point it's an empty shell with no OS.

2. **Bring in an OS** — rather than running an installer, you import a pre-built "cloud image" (a disk that already has a minimal OS installed and is designed to accept automatic configuration on first boot).

3. **Attach the disk properly** — importing data and actually wiring it into the VM as a usable drive are two separate concerns. Attaching it also means choosing a controller type (VirtIO vs. older emulated controllers), which affects performance.

4. **Add a configuration channel (Cloud-Init)** — a small special-purpose drive that isn't an OS disk, but carries instructions like hostname, network settings, and SSH keys, applied automatically the first time the VM boots. This is what makes the same template produce many differently-configured VMs.

5. **Set boot priority** — having a disk attached doesn't mean the VM knows to boot from it, especially with multiple drives present (the OS disk vs. the Cloud-Init drive). This step removes that ambiguity.

6. **Console output** — cloud images assume a headless server model (no monitor), so they send output to a serial channel rather than a virtual graphics card. You align the VM's console viewer with that expectation, or you'd see a blank screen.

7. **Convert to template** — lock it down as read-only, ready to clone.

### VirtIO

A device model built for virtualization rather than emulating real hardware. Since both sides know it's virtual, communication is direct and efficient rather than "pretending" to be a real network card or disk controller. The tradeoff: the guest OS needs drivers that understand this virtual protocol (standard in Linux, requires extra steps in Windows).

### Storage Concepts (LVM)

There's a layered hierarchy underneath "the disk Proxmox gives your VM":

- **Physical Volume** — a real disk that's been "claimed"/labeled so LVM can manage it.
- **Volume Group** — a combined pool of one or more physical volumes; the physical boundaries of individual disks disappear once merged in.
- **Logical Volume** — an actual usable chunk carved out of that pool — this is what ends up as a VM's virtual disk.

Proxmox's default `local-lvm` storage is really one particular logical volume (a thin pool) that itself contains many smaller logical volumes — one per VM disk. Importing a VM's disk image doesn't create a new pool; it creates a new volume inside the existing pool, shared with every other VM's disk.

### Thin Provisioning & Capacity

Because space is only consumed as data is actually written (not reserved upfront), you can allocate more virtual disk space than physically exists. This is efficient but has no built-in safety net — there's no automatic warning system beyond what you configure yourself, and there are actually two ways a thin pool can run out:

- Exhausting the actual data space
- Exhausting the separate metadata space that tracks block ownership (more common with heavy snapshotting/cloning)

Either can make the whole pool misbehave, not just the one VM that triggered it.

### Adding a New Disk

Two different intentions lead to two different approaches:

- **Merge it into existing storage** — the new disk becomes part of the same pool, so existing VM disks can grow larger over time.
- **Keep it separate** — useful for isolation (so one runaway VM can't consume all your storage), but VM disks living in one pool can't be resized using space from the other. A VM could still gain more total storage by getting an entirely separate additional disk from the new pool — just not by growing its original disk.

### Cloud-Init Credentials

If you don't configure a password, Cloud-Init doesn't fall back to anything insecure — it simply doesn't set one. Cloud images assume key-based SSH login as the real authentication method, with password login disabled by default as a security practice. A password is really just an optional emergency/console fallback, not the primary access method.

## What caused confusion / what fixed it

- Initially unclear whether importing a disk and attaching it were the same step. They're not — `qm importdisk` copies the data into storage, `qm set --scsi0` wires it as a drive. Two separate concerns.
- The serial console requirement for Cloud-Init wasn't obvious. Without `--serial0 socket --vga serial0`, Cloud-Init still runs but you can't see its output, making it look like it failed.
- LVM thin provisioning has two exhaustion modes (data vs metadata), not just one. Metadata exhaustion is less common but more dangerous because it can happen with heavy clone/snapshot workflows even when data space is fine.
