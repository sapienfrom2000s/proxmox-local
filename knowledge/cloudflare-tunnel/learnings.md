# Cloudflare Tunnel — Learnings

## 2026-07-10

### Why was it needed?

Port forwarding has three problems: CGNAT blocks inbound traffic, opening ports exposes the homelab directly, and dynamic IP + DDNS adds complexity on top.

Cloudflare Tunnel solves all three. It creates an **outbound-only** encrypted tunnel from your homelab to Cloudflare's edge. No inbound ports. No public IP needed. No CGNAT issues.

### How it works

`cloudflared` daemon runs on your homelab and opens a **persistent outbound WebSocket** to Cloudflare's edge. Always on. If it drops, it reconnects automatically. No traffic flows until the connection is live.

When a client connects to `app.yourdomain.com`:

```
Client                    Cloudflare Edge              cloudflared           localhost:8080
  │                            │<──(outbound WebSocket)────│  ← cloudflared opens
  │                            │   (always on)             │                      │
  │                            │                           │                      │
  │──TCP+TLS handshake────────>│                           │                      │
  │──HTTP request─────────────>│                           │                      │
  │                            │──(lookup tunnel)─────────>│                      │
  │                            │──(send via WebSocket)────>│                      │
  │                            │                           │──new TCP connect────>│
  │                            │                           │──HTTP request───────>│
  │                            │                           │<──HTTP response──────│
  │                            │<──(send via WebSocket)────│                      │
  │<──HTTP response────────────│                           │                      │
```

Two separate TCP connections: client↔Cloudflare and cloudflared↔local service. `cloudflared` bridges them. Cloudflare never talks directly to your service.

**Why this works through CGNAT:** `cloudflared` initiates the connection outbound. CGNAT tracks it in its state table and allows return traffic on the same flow. Same mechanism as your browser visiting a website. CGNAT doesn't know about Cloudflare — it just sees an outbound TCP connection to port 443.

### SSH through Cloudflare Tunnel

Same outbound tunnel, but TCP instead of HTTP. Client uses `cloudflared` as ProxyCommand to wrap SSH traffic through the tunnel:

```bash
ssh -o ProxyCommand="cloudflared access ssh --hostname %h" user@ssh.yourdomain.com
```

```
Client's cloudflared        Cloudflare Edge         Homelab's cloudflared      localhost:22
       │                         │<──(outbound WS)─────│  ← always on             │
       │                         │                     │                          │
       │──TCP connect───────────>│                     │                          │
       │──SSH init──────────────>│                     │                          │
       │                         │──(lookup tunnel)───>│                          │
       │                         │──(send via WS)─────>│                          │
       │                         │                     │──new TCP connect────────>│
       │                         │                     │──SSH init───────────────>│
       │                         │                     │<──SSH banner─────────────│
       │                         │<──(send via WS)─────│                          │
       │<──SSH banner────────────│                     │                          │
       │                         │                     │                          │
       │  ...key exchange...     │                     │   ...key exchange...     │
       │                         │                     │                          │
```

Three parties: client's `cloudflared` (ProxyCommand), Cloudflare edge, and homelab's `cloudflared` → SSH daemon. The SSH client's `cloudflared` wraps the connection and sends it through Cloudflare, homelab's `cloudflared` unwraps it and connects to the local SSH daemon.
