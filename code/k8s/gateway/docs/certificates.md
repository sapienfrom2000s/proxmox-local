# Certificates

## How root and leaf certificates relate

There are two separate private keys:

1. The root CA's private key — used only to sign other certificates. Never
   shared, never leaves its Secret.
2. The leaf certificate's private key — generated per service, used by that
   service to handle TLS traffic.

They are not derived from each other. The connection is the **signature**:

- The root CA's private key creates a digital signature
- That signature is embedded in the leaf certificate
- The leaf certificate also contains its own public key
- The leaf's private key is stored separately with the service

When a client receives the leaf certificate, it uses the root CA's public key
(which it already trusts) to verify the signature. If valid, the client knows
the leaf was issued by a trusted authority.

```
  home-ca (root CA)
       │
       │ signs with its private key
       │ creates a signature embedded in the cert
       ▼
  home-wildcard (leaf cert)
       │
       │ contains:
       │  - its own public key
       │  - the signature from home-ca
       │  - SANs: *.home, home, todo.home
       │
       │ served during TLS handshake
       ▼
  Client verifies signature using home-ca's public key
```

---

## Wildcard certificate

A single certificate covers all `*.home` services:

```
  certificate.yaml
  ┌──────────────────────────────────────────┐
  │ name: home-wildcard                      │
  │ secretName: home-tls                     │
  │ dnsNames:                                │
  │   - "*.home"                             │
  │   - "home"                               │
  │   - "todo.home"    ← explicit entry     │
  │ issuerRef: ca-issuer (ClusterIssuer)     │
  └──────────────────────────────────────────┘
```

cert-manager signs it using the root CA, stores cert + key in Secret `home-tls`,
and auto-renews it. The Gateway references this Secret for TLS.

---

## Why explicit hostnames

The wildcard `*.home` should match `todo.home` per RFC 6125, but some clients
(Safari, curl with SecureTransport) reject wildcard matching. Adding explicit
entries like `todo.home` avoids this.

---

## Trust chain

```
  home-ca (root CA)
       │  trusted by OS/browser
       │  signs leaf certs
       ▼
  home-wildcard (*.home)
       │
       ├── todo.home
       ├── dashboard.home
       └── any *.home service
```

Root CA must be imported into:

- macOS Keychain (Safari, system curl)
- Firefox cert store (Settings → Certificates → Authorities → Import)
