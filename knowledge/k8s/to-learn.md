Q. How etcd allows only kube-api server to talk to it directly? How can it be
overridden?

### OIDC -> from kube-apiserver, kubectl via oidc

For humans. You configure an OIDC provider (Dex, Google, GitHub), and the API
server validates JWTs from that provider. Your identity and group memberships
come from the token claims. This is how production clusters let engineers use
kubectl without sharing certs — you authenticate with your SSO, and the API
server trusts the identity your provider vouches for.

**If authentication fails:** 401 Unauthorized. The request stops. No further
processing.
