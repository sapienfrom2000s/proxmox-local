# External HTTPS — Browser to Cluster

## The problem

kubeadm's certificates handle internal mTLS — components inside the cluster
authenticating to each other (kubelet → API server, API server → etcd, etc.).
See [kube-apiserver/authentication.md](../kube-apiserver/authentication.md) for
that flow.

This document covers external HTTPS — when a browser connects to a service
running in your cluster. These are two different trust domains:

```
┌─────────────────┬──────────────────────┬────────────────────────────────────┐
│                 │ Internal mTLS        │ External HTTPS                     │
├─────────────────┼──────────────────────┼────────────────────────────────────┤
│ **Who**         │ Cluster components   │ Browsers, CLI tools                │
├─────────────────┼──────────────────────┼────────────────────────────────────┤
│ **Trusts what** │ Cluster CA (ca.crt)  │ OS/browser trust store             │
├─────────────────┼──────────────────────┼────────────────────────────────────┤
│ **Signed by**   │ kubeadm CA           │ Let's Encrypt, self-signed, org CA │
├─────────────────┼──────────────────────┼────────────────────────────────────┤
│ **Purpose**     │ Component-to-comp    │ User-facing encryption             │
└─────────────────┴──────────────────────┴────────────────────────────────────┘
```

## The flow

```
┌─────────┐                  ┌────────────────┐               ┌─────────────┐
│ Browser │                  │ TLS Terminator │               │ Backend Pod │
└────┬────┘                  └───────┬────────┘               └──────┬──────┘
     │                               │                               │
     │─── HTTPS request ────────────>│                               │
     │    (e.g., https://myapp)      │                               │
     │                               │                               │
     │<─── TLS certificate ──────────┤                               │
     │    (presents cert)            │                               │
     │                               │                               │
     │ ┌───────────────────────────┐ │                               │
     │ │ Browser validates:        │ │                               │
     │ │  - Is cert expired?       │ │                               │
     │ │  - Is hostname correct?   │ │                               │
     │ │  - Is CA trusted?         │ │                               │
     │ │    (via OS trust store)   │ │                               │
     │ └─────────────┬─────────────┘ │                               │
     │               │               │                               │
     │ (If all pass) ▼               │                               │
     │<═══ HTTPS established ═══════>│                               │
     │                               │                               │
     │                               │─── HTTP request ─────────────>│
     │                               │    (plain HTTP, internal)     │
     │                               │                               │
     │                               │<─── response ─────────────────┤
     │                               │                               │
     │<─── HTTPS response ───────────┤                               │
     │                               │                               │
```

Step by step:

1. Browser sends HTTPS request to the TLS terminator (port 443)
2. TLS terminator presents its certificate
3. Browser validates the certificate:
   - Is it expired?
   - Does the hostname match?
   - Is the signing CA in the OS trust store?
4. If all pass → HTTPS connection is established
5. TLS terminator routes traffic to the backend pod (plain HTTP internally)
6. Response flows back through the same path

TLS terminates at the edge. Traffic inside the cluster is plain HTTP. This is
the standard pattern — no need for TLS on the private network inside the
cluster.

## How browsers decide to trust a certificate

A certificate is just a public key + identity + CA signature. The browser trusts
it if:

1. Certificate chain is valid — cert → intermediate CA → root CA
2. Root CA is in the OS trust store — macOS Keychain, Linux ca-certificates,
   Windows cert store
3. Hostname matches — the domain in the URL matches the cert's Subject
   Alternative Name (SAN)
4. Not expired — `notBefore` < now < `notAfter`

If any check fails → browser shows "Your connection is not private" warning.

## Self-signed certificates

For a homelab, Let's Encrypt won't work (needs public DNS). The options:

Ad-hoc self-signed: Generate a cert directly. Browser warns every time because
the signing CA is unknown. Must click "Advanced" → "Proceed" each visit.

Own CA, trusted once: Create a root CA, install it in your OS trust store
(one-time). Any cert signed by your CA is then trusted. No browser warnings.
This is what cert-manager automates — it creates a CA for you, issues certs from
it, and handles renewal.

## Why two different CAs?

You end up with two CAs in your cluster:

```
┌─────────────┬──────────────────────────┬───────────────────────────────────┐
│ CA          │ What it signs            │ Who trusts it                     │
├─────────────┼──────────────────────────┼───────────────────────────────────┤
│ kubeadm CA  │ API server, kubelet, etcd│ Cluster components (internal mTLS)│
├─────────────┼──────────────────────────┼───────────────────────────────────┤
│ External CA │ TLS certs for external   │ Browsers (OS trust store)         │
│             │ services                 │                                   │
└─────────────┴──────────────────────────┴───────────────────────────────────┘
```

They're independent. The kubeadm CA never signs external certs, and the external
CA never signs cluster component certs. Different trust domains, different keys.

## See also

- [kube-apiserver/authentication.md](../kube-apiserver/authentication.md) —
  internal mTLS flow (kubeadm CA, component-to-component auth)
