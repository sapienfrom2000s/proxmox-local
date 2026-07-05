output "vm_ips" {
  description = "IP addresses of the provisioned VMs"
  value = {
    for k, vm in proxmox_virtual_environment_vm.vm : k => vm.ipv4_addresses
  }
}

output "vm_ids" {
  description = "Proxmox VM IDs"
  value = {
    for k, vm in proxmox_virtual_environment_vm.vm : k => vm.id
  }
}
