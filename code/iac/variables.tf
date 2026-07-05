variable "proxmox_endpoint" {
  type        = string
  description = "Proxmox VE API endpoint URL (e.g. https://192.168.1.9:8006/api2/json)"
}

variable "api_token" {
  type        = string
  sensitive   = true
  description = "Proxmox API token ID and secret (e.g. tofu@pve!tofu-token=uuid)"
}

variable "skip_tls_verify" {
  type        = bool
  default     = false
  description = "Skip TLS certificate verification (enable for self-signed certs)"
}

variable "pm_node" {
  type        = string
  default     = "pve"
  description = "Proxmox node name"
}

variable "template_id" {
  type        = number
  default     = 9000
  description = "ID of the pre-created VM template to clone from"
}

variable "ssh_public_key" {
  type        = string
  description = "Public SSH key injected into VMs via Cloud-Init"
}

variable "vm_bridge" {
  type        = string
  default     = "vmbr0"
  description = "Network bridge for VMs"
}

variable "gateway_ip" {
  type        = string
  default     = "192.168.1.1"
  description = "Gateway IP address (typically your router)"
}

variable "dns_servers" {
  type        = list(string)
  default     = ["1.1.1.1", "8.8.8.8"]
  description = "Upstream DNS servers for VMs"
}

variable "vm_username" {
  type        = string
  default     = "debian"
  description = "Default Cloud-Init user created on VMs"
}
