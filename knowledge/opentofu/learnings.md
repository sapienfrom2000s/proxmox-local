# OpenTofu — Learnings

## 2026-07-03

### What I actually understand

**The core mental model**: OpenTofu is a reconciliation engine. You describe the desired state in code, and it figures out the diff between that and what actually exists (tracked in the state file), then makes the API calls to close the gap.

**The four things that matter day-to-day:**

1. `resource` vs `data`
   - `resource` = "create/manage this thing"
   - `data` = "look up this existing thing so I can reference it"
   - The distinction clicked when I realized `data` doesn't touch anything — it's read-only.

2. `variable` and `output`
   - `variable` = inputs (parameterize your config, don't hardcode)
   - `output` = what gets printed after apply (useful for IPs, IDs you need next)

3. The state file (`terraform.tfstate`)
   - It's how OpenTofu knows what it created. If it's out of sync with reality, bad things happen.
   - For a single-node homelab, local state is fine. No need for remote backends yet.

4. The four commands
   - `tofu init` → download providers
   - `tofu plan` → show what would change (always run this first)
   - `tofu apply` → actually make the changes
   - `tofu destroy` → tear everything down

**How it connects to Proxmox**: OpenTofu doesn't talk to Proxmox directly — it uses the `bpg/proxmox` provider plugin, which translates resource declarations into Proxmox VE API calls.

### What caused confusion / what fixed it

- Initially unclear whether `data` sources could modify things. Fixed by: they can't — `data` is always read-only, even if the underlying API supports writes.
- The state file felt like a black box. Fixed by: opening it and reading it — it's just JSON mapping resource addresses to real IDs.
