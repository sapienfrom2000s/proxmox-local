# Secrets Management — Learnings

## 2026-07-08

### Why you need one — what's wrong with the alternatives

**Hardcoded values in source code**
```python
db = connect("postgres://admin:password123@db:5432/app")
```
- Committed to git → lives in history forever, even after removal
- Every developer sees prod credentials
- Rotating means a code change, PR, deploy cycle

**.env files (slightly better, still flawed)**
- Kept out of git via `.gitignore` — better, but:
  - Shared by copy-paste ("here's the .env file") — no access control
  - No audit trail — who has it? Who used it? Unknown
  - Rotation means notifying every teammate to update their local file
  - Laptop stolen? All secrets are in plaintext on disk

**Shared documents / password managers**
- "What's the DB password?" — answer is in a wiki page or 1Password vault
- No machine access — can't be used by CI/CD or automated processes
- No versioning — rollback means "find the old email"

**Environment variables set in CI/CD dashboards**
- Better isolation, but configured manually per platform
- No single source of truth — same secret repeated in GitHub Actions, GitLab CI, Vercel, etc.
- No audit — CI platform logs who changed it, but that's not designed for secrets governance

### What a secrets manager actually solves

- **Single source of truth**: one place to store, rotate, and audit every secret
- **Access boundaries**: devs see dev, ops see prod, auditors see everything. Fine-grained RBAC.
- **Audit trail**: every read, write, delete logged — who, when, from where
- **Rotation without downtime**: update in one place, all consumers pick it up live or on next fetch
- **Machines can use it too**: service tokens for CI/CD, K8s operators, CLI injection — not just humans
- **Encryption everywhere**: at rest (AES-256), in transit (TLS), often with BYOK options
- **Breach containment**: if a laptop or CI log leaks a secret, dynamic secrets auto-revoke. Static secrets can be rotated centrally in seconds

### What happens if the secrets manager itself goes down

This is the #1 counter-argument to using a remote secrets manager, and it's valid.

**Without a secrets manager (e.g., .env files):**
- Secrets are on disk. No network dependency. Works offline, always.
- But: no rotation, no audit, no access control, no revocation.

**With a remote secrets manager:**
- `doppler run -- <cmd>` fetches secrets via API before starting the process.
- If Doppler is unreachable, the command **fails** — nothing starts.

**Mitigations:**

1. **Fallback files (Doppler's solution)**
   - Every `doppler run` automatically writes an encrypted snapshot to disk (AES-256-GCM, keyed to your Doppler token).
   - On subsequent runs, if the API is unreachable, the CLI **falls back** to the cached file.
   - Can be forced with `--fallback-only` to never call the API at all (air-gapped deploys).
   - Downside: the fallback is only as fresh as the last successful `doppler run`. Rotated secrets won't be picked up until the API is reachable again.

2. **Kubernetes Operator syncs (for Phase 2)**
   - The operator pulls secrets once and materializes them as native K8s `Secret` objects.
   - If Doppler goes down, pods keep running with the last synced values. No disruption.
   - Downside: secrets are stale until the operator can re-sync.

3. **High availability guarantees**
   - Most vendors (Doppler included) offer 99.99% uptime SLA.
   - Outages happen, but they're rare and usually measured in minutes, not hours.

**The real trade-off:**
- Uptime dependency vs. the security benefits you get in exchange.
- For a homelab: the dependency doesn't matter much — if Doppler is down, `tofu apply` fails, you wait, retry.
- For production: fallback files + K8s operator make this a non-issue for running services. The risk window is limited to deploys during an outage.

### What is a secrets manager

A centralized system that stores, controls access to, and audits usage of sensitive values: API tokens, database passwords, SSH keys, TLS certificates, cloud provider credentials. Instead of sitting in config files, .env files, or git history, secrets live in a dedicated store and are fetched at runtime.

### Core features every secrets manager has

**Storage & encryption**
- Secrets encrypted at rest (AES-256) and in transit (TLS)
- Most offer a KMS integration (bring your own key) for enterprises
- Some support hardware security modules (HSM)

**Access control**
- **Users**: individual human identities with login credentials
- **RBAC / Roles**: granular permissions — who can read, write, delete, list secrets. Typically: admin, editor, reader, custom roles
- **Service tokens**: machine-to-machine auth (for CI/CD pipelines, apps) — scoped to a specific project/environment with read-only by default
- **OIDC / SSO**: authenticate via Google, GitHub, Entra ID, Okta — no separate password

**Environments**
- Separate secret sets per environment (dev/staging/prod) within a project
- Prevents a dev from accidentally reading prod credentials
- Promotion workflow: dev → staging → prod with approval gates

**Audit & compliance**
- **Activity logs**: every secret read, write, delete, and access attempt — who did what, when, from which IP
- **Access logs**: drill down to individual secret access over time
- Version history: rollback to any previous value
- SOC 2, ISO 27001, HIPAA certifications common

**Secret rotation**
- Scheduled or on-demand replacement of secrets without downtime
- Some support automated rotation integrated with the source (e.g., auto-rotate a Postgres password and update it everywhere)
- **Dynamic secrets**: create short-lived, auto-revoking credentials (e.g., a DB password valid for 1 hour). If leaked, they expire before they can be abused

**Integration surface**
- CLI for local development — inject secrets as env vars into any process
- REST API for automation
- Native integrations with cloud platforms (AWS, GCP, Azure) and CI/CD (GitHub Actions, GitLab CI)
- Kubernetes operators — sync secrets into the cluster as native `Secret` resources
- IaC providers (Terraform/OpenTofu) — reference secrets in infrastructure code

**Branching / feature workflows**
- Branch configs for per-developer or per-feature sandboxes
- Personal configs (auto-namespaced per developer)
- Config inheritance — share common secrets across projects

### Why it matters in a team

- **Separation of duties**: devs see dev secrets only, ops see prod, auditors get logs
- **Shared context can't happen**: "Hey, what's the production DB password?" — answer is "ask the secrets manager"
- **Secrets aren't in git**: no `.env` files committed, no secrets in CI logs, no blast radius from a repo leak
- **Rotation is practical**: one command, not a ticket to every team member to update their local .env

### Why it's overkill for a single-person homelab

A `.env` file in `.gitignore` achieves nearly everything needed for one person on one machine. The value of a secrets manager starts showing when you have multiple people, multiple environments, compliance requirements, or a need for dynamic/rotating credentials.

### Why I'm using it anyway as a single person

Device loss. If my laptop is stolen or dies, the .env file goes with it. I'd have to remember every secret, regenerate API tokens, and reconstruct from scratch. With Doppler, I authenticate on the new machine and everything is there — no recovery burden, no secrets permanently lost on a dead drive. The convenience of not being tied to a specific physical device justifies the dependency.
