# Carrier-Grade NAT (CGNAT) — Learnings

## 2026-07-10

### Why is CGNAT a problem?

Traditional NAT (home router) translates your private `192.168.x.x` addresses to **one public IP** that you own. With CGNAT, your ISP does a **second layer of NAT** — your "public IP" isn't actually public. It's shared among multiple customers.

This means:

1. **No port forwarding.** You can't punch holes through two layers of NAT. Your router forwards ports to your homelab, but the ISP's CGNAT gateway drops inbound packets because your IP is shared.
2. **DDNS is useless alone.** Even if your domain points to the right IP, traffic never reaches you. DDNS solves DNS; CGNAT blocks the network path.
3. **Peer-to-peer breaks.** Torrents, video calls, online gaming — anything that expects a reachable IP degrades or fails.
4. **VPN tunnels from outside won't connect.** WireGuard/OpenVPN inbound connections can't traverse CGNAT without additional work.

### How to detect CGNAT

- **Compare public vs WAN IP:** Your router's WAN interface IP should match `curl ifconfig.me`. If they differ, you're behind CGNAT.
- **TTL test:** `traceroute` to an external host. If the first hop shows a `10.x.x.x` or `100.64.x.x` address (RFC 6598 shared space), that's the CGNAT gateway.
- **Check your ISP's docs:** Some ISPs explicitly state CGNAT usage on residential plans.

```
# Quick detection
curl ifconfig.me          # your "public" IP
ip addr show ppp0         # your WAN IP (or br0, eth0, etc.)
# If these differ → CGNAT
```

### CGNAT vs regular NAT

| | Regular NAT (home router) | CGNAT (ISP) |
|---|---|---|
| **Where** | Your router | ISP's infrastructure |
| **Private range** | `192.168.x.x`, `10.x.x.x` | `100.64.0.0/10` (RFC 6598) |
| **You control it** | Yes | No |
| **Port forwarding** | Works | Blocked (double NAT) |
| **Public IP** | Yours | Shared among customers |

### Solutions

- **Request a public IP from ISP** — some ISPs offer this for a fee or on request.
- **IPv6** — CGNAT typically only applies to IPv4. If both sides support IPv6, traffic flows end-to-end without NAT.
- **VPN tunnel / VPS relay** — run a small VPS with a public IP, tunnel traffic through it (WireGuard, Tailscale, ZeroTier).
- **ISP migration** — switch to an ISP that doesn't use CGNAT (fiber providers often don't).

### What caused confusion / what fixed it

- Thought CGNAT was the same as regular NAT. Fixed by: regular NAT is one layer you control; CGNAT is a second layer upstream that you can't configure. The key difference is control and the `100.64.0.0/10` address space.
- Assumed DDNS would fix connectivity behind CGNAT. Fixed by: DDNS only ensures DNS resolves to the right IP — it doesn't help if the network path is blocked. CGNAT and DDNS solve different layers of the same problem.
- Thought CGNAT was rare. Fixed by: it's increasingly common on mobile (4G/5G) and some fiber/cable ISPs trying to conserve IPv4 addresses. Many "unlimited data" mobile plans use CGNAT by default.
