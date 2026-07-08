# Proxmox API connection — sensitive values read from Doppler
# See: scripts/tofu.sh
# run: doppler run -- bash scripts/tofu.sh plan
skip_tls_verify = true

# Proxmox node
pm_node = "thirtyone"

# VM template
template_id = 9000

# Networking
vm_bridge   = "vmbr0"
gateway_ip  = "192.168.1.1"
dns_servers = ["1.1.1.1", "8.8.8.8"]

# Cloud-Init
vm_username = "debian"
