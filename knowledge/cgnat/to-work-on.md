# Carrier-Grade NAT (CGNAT) — To Work On

> Things not already tracked in ROADMAP.md. Open questions, half-formed
> understanding, or experiments to run.

## Open Questions

- Does the current homelab ISP use CGNAT? (Need to run the detection steps.)
- If behind CGNAT, is IPv6 available as an alternative? (Some ISPs CGNAT IPv4 but provide native IPv6.)
- How does CGNAT affect WireGuard site-to-site if expanding to multiple nodes in the future?

## Half-Formed Understanding

- CGNAT address space (`100.64.0.0/10`) looks like a regular private IP but is specifically allocated for ISP shared NAT — need to remember this range when diagnosing.
- Tailscale/ZeroTier abstract away CGNAT by using relay nodes, but at the cost of added latency.

## Experiments to Run

- [ ] Detect CGNAT: compare `curl ifconfig.me` with router WAN IP
- [ ] Test `traceroute` TTL to identify CGNAT gateway hop
- [ ] Check if ISP offers static/public IPv4 as an add-on
