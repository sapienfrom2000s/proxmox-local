locals {
  vms = {
    cp = {
      name   = "cp"
      memory = 2048
      disk   = 20
      ip     = "192.168.1.10/24"
      cores  = 2
    }
    alpha = {
      name   = "alpha"
      memory = 3072
      disk   = 30
      ip     = "192.168.1.11/24"
      cores  = 2
    }
    beta = {
      name   = "beta"
      memory = 3072
      disk   = 30
      ip     = "192.168.1.12/24"
      cores  = 2
    }
  }
}

resource "proxmox_virtual_environment_vm" "vm" {
  for_each = local.vms

  name      = each.value.name
  node_name = var.pm_node

  clone {
    vm_id   = var.template_id
    retries = 3
  }

  cpu {
    cores = each.value.cores
  }

  memory {
    dedicated = each.value.memory
  }

  disk {
    datastore_id = "local-lvm"
    file_format  = "raw"
    interface    = "scsi0"
    size         = each.value.disk
  }

  network_device {
    bridge = var.vm_bridge
    model  = "virtio"
  }

  initialization {
    ip_config {
      ipv4 {
        address = each.value.ip
        gateway = var.gateway_ip
      }
    }

    dns {
      servers = var.dns_servers
    }

    user_account {
      keys     = [var.SSH_PUBLIC_KEY]
      username = var.vm_username
    }
  }

  operating_system {
    type = "l26"
  }
}
