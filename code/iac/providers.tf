provider "proxmox" {
  endpoint  = var.PROXMOX_ENDPOINT
  api_token = var.API_TOKEN
  insecure  = var.skip_tls_verify

  ssh {
    agent    = true
    username = "root"
  }
}
