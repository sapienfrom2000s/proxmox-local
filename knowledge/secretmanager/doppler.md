# Doppler — The Chosen Implementation

## 2026-07-08

### Platform model

| Concept | Doppler equivalent |
|---|---|
| Project | A service or microservice (e.g., `proxmox-local`) |
| Config | An environment: `dev`, `stg`, `prd` (3 defaults, more can be added) |
| Branch config | A fork of a config — `dev_stripe_billing` — for feature work or personal sandbox |
| Config inheritance | One config pulls secrets from another project's config (e.g., shared infra) |
| Secret | A key=value pair within a config |
| Service token | Machine auth — scoped to one config, read-only by default |
| Personal config | Auto-created `dev_personal` branch per user — only they can see it |

### CLI workflow

```bash
# Auth (one-time)
doppler login

# Per-project setup (one-time)
doppler setup  # interactive — picks project and config

# CRUD secrets
doppler secrets set PROXMOX_API_TOKEN=pve-token-xxx
doppler secrets get PROXMOX_API_TOKEN
doppler secrets list

# Run with secrets injected as env vars
doppler run -- tofu apply

# Switch configs
doppler configure set config=dev_stripe_billing
```

The `doppler run` command is the key insight: it fetches secrets from Doppler cloud, injects them as environment variables into the subprocess, and they're gone when the process exits. Nothing touches disk.

### How it maps to the homelab

**Phase 1.3 plan:**
1. Create a Doppler project called `proxmox-local`
2. Store `PROXMOX_API_TOKEN` and `SSH_PRIVATE_KEY` in the `dev` config
3. Wire OpenTofu to read from environment variables (via `TF_VAR_*` or `var.*` with env defaults)
4. Run everything through `doppler run -- tofu apply`

### Permissions model

- **Owner**: full access, billing, workplace settings
- **Admin**: full access except billing and workplace deletion
- **Member**: read/write to assigned projects (can be further scoped)
- **Viewer**: read-only
- **Custom roles**: fine-grained — can specify exactly which actions on which resource types

Service tokens are the most restricted — typically read-only to a single config, used in CI/CD.

### Audit capabilities

- **Activity logs**: every action (create/read/update/delete) on secrets, configs, projects — who, what, when, IP
- **Access logs**: per-secret access history
- **Exportable** via API, webhook, or log streaming to Datadog/Splunk/Slack/SQS
- SOC 2 and ISO 27001 certified

### General features

| Feature | Supported |
|---|---|
| CLI injection | `doppler run -- <cmd>` |
| Secret versioning & rollback | Yes |
| Environments (dev/stg/prd) | Yes (3 defaults) |
| Branch configs | Yes |
| Config inheritance | Yes (Team plan+) |
| RBAC | Yes (custom roles available) |
| Service tokens | Yes (OIDC-scoped optionally) |
| SAML SSO / SCIM | Yes |
| MFA | Yes |
| Dynamic secrets | Yes (AWS IAM, Azure SP, GCP SA) |
| Automated rotation | Yes (AWS RDS, GCP Cloud SQL, others) |
| K8s Operator | Yes (syncs to native Secrets) |
| External Secrets Operator | Yes (provider) |
| Terraform/OpenTofu provider | Yes |
| MCP server | Yes (AI agents can request secrets) |
| Log streaming | Slack, Datadog, Splunk, SQS, HTTPS |
| Uptime SLA | 99.99% |
| Free tier | Yes (limited team members/features) |

### Downsides / trade-offs

- **Cloud dependency**: if Doppler is down or unreachable, local operations that need secrets fail. No offline mode.
- **CLI requirement**: every machine that runs `tofu apply` needs `doppler` installed and authenticated.
- **Internet required**: can't provision in an air-gapped environment.
- **Free tier limits**: limited seats and features (config inheritance is Team plan+).

### Key differentiators from alternatives

- **vs. HashiCorp Vault**: Doppler is SaaS, zero infra to run. Vault is self-hosted, more flexible, more complex.
- **vs. AWS Secrets Manager / GCP Secret Manager**: cloud-locked. Doppler is cloud-agnostic.
- **vs. sops+age**: Doppler is a live service with audit and RBAC. sops is file-based encryption in git — simpler but no access controls.
- **vs. Ansible Vault**: Doppler doesn't require Ansible, works with any tool. Ansible Vault is file-based and tied to the Ansible ecosystem.
