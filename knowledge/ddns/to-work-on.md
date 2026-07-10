# Dynamic DNS (DDNS) — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed
> understanding, or experiments to run.

## Open Questions

- Does the Proxmox host itself need DDNS, or should it be a specific VM? (Depends on what needs to be reachable from outside — WireGuard endpoint on the host vs. reverse proxy in a VM.)
- If using Cloudflare DDNS, is the API token scoped to DNS-only edits, or does it need broader permissions? What's the最小 scope?
- How does DDNS interact with a future K3s ingress? Does the domain point to the node IP or a LoadBalancer VIP?

## Half-Formed Understanding

- TTL values: lower = faster propagation but more DNS queries. For a homelab with a single IP, what's the sweet spot? (60s seems aggressive, 300s probably fine.)
- Some providers (No-IP) require periodic hostname "confirmation" — need to understand if this applies to all free tiers or just certain ones.

## Experiments to Run

- [ ] Compare IP detection reliability: `ifconfig.me` vs `icanhazip.com` vs `api.ipify.org` vs router WAN interface directly
- [ ] Test DDNS propagation time: update a DuckDNS record and measure how long until `dig` resolves the new IP from an external machine
- [ ] Evaluate `ddclient` vs a simple cron script for complexity vs. reliability tradeoff
