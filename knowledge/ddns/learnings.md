# Dynamic DNS (DDNS) — Learnings

## 2026-07-10

### Why is DDNS needed?

Home internet connections almost always come with a **dynamic public IP** — your ISP assigns one from a pool, and it changes periodically (on router reboot, lease expiry, or ISP-side reshuffling). This means:

1. **You can't point a domain to your homelab reliably.** If you buy `myhomelab.com` and set an A record to `1.2.3.4`, that record becomes stale the moment your ISP rotates your IP. Now nothing reaches your services.

2. **Remote access breaks silently.** You set up WireGuard, a reverse proxy, or email from your homelab — all of it assumes a known public IP. When it changes, you're locked out with no error message until you manually check.

3. **No static IP without paying extra.** Most residential ISPs either don't offer static IPs or charge a premium for one. DDNS solves this for free (or nearly free).

**DDNS = Dynamic DNS.** A small client runs somewhere in your network, detects when your public IP changes, and updates a DNS A record automatically. Your domain always resolves to the correct IP without manual intervention.

### How it works (conceptual flow)

```
┌──────────────────────────────────────────────────────────┐
│  Home Network                                            │
│                                                          │
│  ┌─────────────┐     ┌──────────────┐                    │
│  │ DDNS Client  │────>│ DDNS Provider │──> DNS record     │
│  │ (checks IP)  │     │ (API call)    │    updated        │
│  └─────────────┘     └──────────────┘                    │
│        │                                                  │
│        │ detects public IP change                         │
│        ▼                                                  │
│  ┌─────────────┐                                          │
│  │   Router /   │  ← ISP-assigned dynamic IP              │
│  │   Host       │                                         │
│  └─────────────┘                                          │
└──────────────────────────────────────────────────────────┘
```

1. A **client** periodically checks the network's public IP (by hitting an external service like `ifconfig.me`, or reading the router's WAN interface directly).
2. If the IP has changed, the client calls the DDNS provider's **API** to update the DNS A record.
3. The DNS provider propagates the change. TTL is typically low (60s–300s) so clients worldwide see the new IP quickly.

### DDNS Providers

- DuckDNS
- No-IP
- Cloudflare
- FreeDNS (afraid.org)
- Dynu
- Google Domains / Cloud DNS

### Update Methods

- **Cron job** — Shell script checks IP periodically, calls provider API if changed.
- **Systemd timer** — Same as cron but with better logging and dependency control.
- **Router built-in** — Many routers (Asus, pfSense, OPNsense, OpenWrt) support DDNS natively.
- **Client daemon** — `ddclient`, `inadyn`, or provider-specific snaps handle retries and IP detection.
- **In-cluster CronJob** — K3s CronJob runs the update script in a container.

### ddclient — the most common dedicated client

`ddclient` is the de facto open-source DDNS client. It supports dozens of providers out of the box, runs as a daemon or via cron, and handles:

- IP detection (via multiple services)
- Protocol translation (each provider has a different update API)
- Retry logic and logging
- Running on Linux, BSD, macOS

```bash
# /etc/ddclient.conf example for DuckDNS
daemon=300                    # check every 5 minutes
syslog=yes
pid=/var/run/ddclient.pid
ssl=yes
use=web, web=ifconfig.me/ip
protocol=duckdns
server=www.duckdns.org
login='home'
password='your-token-here'
```

### What caused confusion / what fixed it

- Assumed DDNS and "static IP from ISP" were the same thing. Fixed by: they solve the same problem (reachable hostname) through completely different mechanisms — one keeps DNS in sync with a changing IP, the other prevents the IP from changing in the first place. Static IP costs money; DDNS costs nothing but adds a propagation delay window (TTL) where the old IP might still be cached.
- Thought DDNS was only for exposing services to the internet. Fixed by: it's also useful internally — if your ISP rotates your IP, even VPN tunnels or reverse SSH connections break. DDNS keeps those stable too, even if you never open a port to the public internet.
- Confused DuckDNS "domains" with owning a domain. Fixed by: DuckDNS gives you a subdomain (`something.duckdns.org`), not a full domain. If you want `myhomelab.com`, you need a real registrar + a provider that supports custom domains (Cloudflare, Dynu, etc.).
