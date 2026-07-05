proxmox_endpoint = "https://192.168.1.9:8006/api2/json"
api_token        = "c5b506ed-8f73-4bd7-b88b-05fbdc5e773c"
skip_tls_verify  = true

pm_node     = "thirtyone"
template_id = 9000

ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDF7Bgz85LYbTN5TwITFCosrweH5bKJfyS/MtfJLnO8+"

vm_bridge   = "vmbr1"
gateway_ip  = "192.168.1.1"
dns_servers = ["1.1.1.1", "8.8.8.8"]

vm_username = "debian"
