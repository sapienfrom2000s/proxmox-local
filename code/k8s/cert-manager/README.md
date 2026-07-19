# cert-manager

Automated certificate management for Kubernetes. Issues TLS certificates from an
in-cluster CA — no external services, no manual renewals.

## Why

`.home` is not a public TLD, so Let's Encrypt won't issue certificates for it.
cert-manager with a self-signed CA solves this: it creates its own root
certificate, stores it in-cluster, and issues certs for any domain you define.

## How it works

```
self-signed issuer (built-in bootstrap)
    └─> issues CA cert (root of trust, stored as Secret)
            └─> CA issuer uses that CA cert to sign
                    └─> wildcard cert for *.home (stored as Secret)
```

1. **selfsigned-issuer** — ClusterIssuer that issues self-signed certificates
   (used only once, to bootstrap the CA)
2. **home-ca** — Certificate resource that creates a CA cert via the self-signed
   issuer. The CA key+cert are stored in Secret `home-ca-ca`
3. **ca-issuer** — ClusterIssuer that references the CA Secret. All real
   certificates are signed by this issuer
4. **home-wildcard** — Certificate resource requesting `*.home`. The resulting
   TLS cert+key are stored in Secret `home-tls`

## Installation

```bash
# 1. Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.21.0/cert-manager.yaml

# 2. Apply issuers + wildcard cert
kubectl apply -f code/k8s/cert-manager/issuers.yml
kubectl apply -f code/k8s/cert-manager/wildcard.yml
```

## Secrets produced

| Secret       | Namespace      | Contains                                            |
| ------------ | -------------- | --------------------------------------------------- |
| `home-ca-ca` | `cert-manager` | CA root cert + key (`tls.crt`, `tls.key`, `ca.crt`) |
| `home-tls`   | `default`      | Wildcard TLS cert + key for `*.home`                |

Any Ingress or Service can reference `home-tls` for TLS termination.

## Trusting the CA on your Mac

Browsers won't trust the self-signed CA out of the box. Extract and install it:

```bash
# 1. Extract the CA cert
kubectl get secret home-ca-ca -n cert-manager -o jsonpath='{.data.ca\.crt}' \
  | base64 -d > home-ca.crt

# 2. Add to macOS Keychain (System keychain, always trust)
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain home-ca.crt

# 3. Clean up
rm home-ca.crt
```

After this, `https://nginx.home`, `https://grafana.home`, etc. will show as
secure in your browser.

## Verifying

```bash
# Check issuers are Ready
kubectl get clusterissuers

# Check certificate status
kubectl get certificates -A

# Inspect the wildcard cert
kubectl describe secret home-tls
```

## Files

```
code/k8s/cert-manager/
├── install.yml     # cert-manager manifest reference
├── issuers.yml     # selfsigned-issuer → CA cert → ca-issuer
├── wildcard.yml    # *.home Certificate resource
└── README.md       # This file
```

## Renewal

cert-manager handles renewal automatically. The wildcard cert is set to:

- **Duration**: 1 year (8760h)
- **Renew before**: 30 days (720h)

The CA cert is set to:

- **Duration**: 10 years (87600h)
- **Renew before**: 1 year (8760h)

No manual intervention needed — cert-manager creates new CertificatesRequest
objects and updates the Secrets before expiry.
