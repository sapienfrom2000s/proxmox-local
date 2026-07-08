# Secrets Management — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed understanding, or experiments to run.

## Open Questions

- What's the failure mode if Doppler is unreachable during `tofu apply`? Does the CLI block, timeout, or fall back to cached values?
- Can a service token be scoped to individual secrets within a config, or is it all-or-nothing per config?
- How does Doppler handle concurrent edits — last-write-wins, or is there locking?

## Half-Formed Understanding

- **Dynamic Secrets in practice**: The concept is clear (short-lived auto-revoking creds), but I don't understand the implementation flow — does the client make a separate API call per credential, or does `doppler run` handle it transparently?
- **Doppler Kubernetes Operator**: Understands the idea (syncs secrets into K8s), but haven't seen the CRD spec or the reconciliation loop logic.
- **Config inheritance across workplaces**: Not sure if this is possible or if inheritance is limited to within one workplace.

## Experiments to Run

- [ ] Create a Doppler project, set a few test secrets, run `doppler run -- env | grep DOPPLER` to confirm injection works.
- [ ] Delete a secret from the dashboard, re-run the same command — verify live propagation without re-auth.
- [ ] Create a branch config, override one value, confirm the override takes precedence over root config.
- [ ] Intentionally revoke a service token, then try to use it — observe the error message and behavior.
- [ ] Create a service token with read-only access to one config, then try to write — confirm it fails.
