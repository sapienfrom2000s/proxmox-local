# OpenTofu — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed understanding, or experiments to run.

## Open Questions

- What actually happens if the state file gets deleted? Does `tofu import` recover it, or do you have to destroy and recreate everything?
- What does `tofu plan` output look like when a resource drifts (someone changed something in Proxmox UI directly)? Does it detect it?
- When the Proxmox provider does an API call, where do I see logs if something fails? Is there a `TF_LOG` equivalent for provider-level errors?

## Half-Formed Understanding

- **Remote state**: Understand conceptually why it matters for teams (locking, shared view), but haven't touched it. Not needed yet, but worth knowing when to reach for it.
- **`moved` blocks**: Saw these mentioned — seems related to renaming resources without destroy/recreate. Don't fully understand the syntax yet.
- **`for_each` vs `count`**: Know `count` creates N copies of the same resource. `for_each` iterates over a map/set. Not sure when you'd prefer one over the other in the Proxmox context.

## Experiments to Run

- [ ] Delete a VM from Proxmox UI (outside of tofu), then run `tofu plan` — see how drift is detected and reported.
- [ ] Intentionally break the state file and see what error you get on next `tofu plan`.
- [ ] Add a `count = 2` to a VM resource and see what gets created — are they named differently?
