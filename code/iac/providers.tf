provider "proxmox" {
  endpoint  = var.proxmox_endpoint
  api_token = var.api_token
  insecure  = var.skip_tls_verify

  ssh {
    agent    = true
    username = "root"
  }
}
