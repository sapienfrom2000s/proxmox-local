#!/bin/bash
set -euo pipefail

export TF_VAR_proxmox_endpoint="$PROXMOX_ENDPOINT"
export TF_VAR_api_token="$PROXMOX_API_TOKEN"
export TF_VAR_ssh_public_key="$SSH_PUBLIC_KEY"

exec tofu "$@"
