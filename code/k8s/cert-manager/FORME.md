# Cert-Manager: How It All Works

## The problem

Every service using HTTPS needs a certificate. For internal homelab services,
you don't want to depend on Let's Encrypt or external CAs. You need your own
private certificate authority running inside your cluster.

cert-manager is the tool that makes this happen.

---

## Core concepts (read this first)

**Certificates and keys come in pairs.** Every certificate has a matching
private key. The certificate is public — you show it to everyone. The private
key is secret — you never share it.

**Signing is not encryption.** When a CA "signs" a certificate, it's not
encrypting anything. It's stamping it with approval. The CA uses its private key
to create a signature that gets embedded in the certificate. Anyone can verify
that signature using the CA's public key. If it checks out, the certificate was
approved by that CA.

**There are two separate private keys in this setup:**

1. The root CA's private key — used only to sign other certificates. Never
   shared, never leaves its Secret.
2. Each service's own private key — generated per service, used by that service
   to handle TLS traffic.

They are not derived from each other. The only connection is the signature: the
root CA's private key creates it, the leaf certificate carries it.

---

## The players

- **selfsigned-issuer** — A temporary bootstrap helper. Signs the root
  certificate once, then you don't need it anymore.

- **home-ca** — The root certificate. The trust anchor for everything. Valid 10
  years, renews at 9.

- **home-ca-secret** — A Kubernetes Secret holding the root certificate and its
  private key. The private key is the stamp used to sign service certificates.

- **ca-issuer** — The everyday signer. Reads the private key from home-ca-secret
  and uses it to sign any new certificate you request.

---

## The flow

**Step 1 — Bootstrap the root CA**

The selfsigned-issuer creates the home-ca certificate. It signs itself (hence
"self-signed"). Once created, cert-manager stores the certificate and its
private key in the home-ca-secret. The selfsigned-issuer's job is done.

**Step 2 — Make the CA operational**

The ca-issuer points to home-ca-secret. It reads the private key and becomes
ready to sign new certificates. This is the issuer you'll use for all your
services.

**Step 3 — Issue a service certificate**

You create a Certificate resource for your service. cert-manager generates a new
key pair for that service, creates a signing request, sends it to ca-issuer,
which signs it with the root CA's private key. The signed certificate and the
service's private key get stored in a new Secret. cert-manager renews it
automatically before expiry.

---

## How services consume the certificates

cert-manager stores the signed certificate and its private key in a Kubernetes
Secret. Your app or Ingress references that Secret. Kubernetes mounts it where
needed. cert-manager keeps it fresh — if expiry approaches, it renews behind the
scenes.

---

## Wildcard certificate for all services

Instead of creating a separate certificate for every service (todo.home,
dashboard.home, etc.), you can create one wildcard certificate that covers them
all.

The file `certificate.yaml` in the gateway directory does exactly this. It
requests a certificate for `*.home` signed by your root CA. cert-manager creates
it, stores the cert + key in a Secret called `home-tls`, and auto-renews it.

Any service using a `*.home` hostname can reference this same Secret for TLS
termination. One certificate, all services covered.

---

## Quick summary

- The root CA is created once via selfsigned-issuer.
- The root CA's private key lives in a Secret, never shared.
- ca-issuer uses that key to sign service certificates.
- Each service gets its own key pair; the root CA signs it.
- The signature is the only link between root and leaf.
- Everything is automatic — creation, renewal, storage.
