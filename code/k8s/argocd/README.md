# ArgoCD

GitOps continuous delivery for Kubernetes. Syncs apps from a Git repo — push a
manifest change, ArgoCD deploys it.

## Installation

```bash
# 1. Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.4.5/manifests/install.yaml

# 2. Expose via LoadBalancer (MetalLB assigns an IP)
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# 3. Disable HTTPS (homelab, no need for TLS)
kubectl patch configmap argocd-cmd-params-cm -n argocd --type merge -p '{"data":{"server.insecure":"true"}}'
kubectl rollout restart deployment argocd-server -n argocd

# 4. Get the admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

## Why the browser shows "insecure" on HTTPS

ArgoCD generates its own self-signed certificate for HTTPS by default. Even
though we have a `*.home` wildcard cert issued by our CA (and the CA is trusted
in macOS Keychain), ArgoCD doesn't use it — it serves its own cert, which the
browser doesn't trust.

Instead of wiring ArgoCD to use our CA cert, we disable HTTPS entirely. This is
a homelab — TLS is unnecessary for a local-only dashboard. The fix:

```
server.insecure: "true"  # in argocd-cmd-params-cm ConfigMap
```

HTTP access on port 80 works without any cert warnings.

## Access

```
http://argocd.home
username: admin
password: (from step 4)
```

## Files

```
code/k8s/argocd/
├── install.yml   # Manifest + LoadBalancer + insecure patch references
└── README.md     # This file
```
