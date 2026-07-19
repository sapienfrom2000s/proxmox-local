# ArgoCD

GitOps continuous delivery for Kubernetes. Syncs your apps from a Git repo —
push a manifest change, ArgoCD deploys it.

## Installation

```bash
# 1. Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.4.5/manifests/install.yaml

# 2. Expose via LoadBalancer (MetalLB assigns an IP)
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# 3. Get the admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

## Access

```
http://<METALLB_IP>
username: admin
password: (from step 3)
```

## Files

```
code/k8s/argocd/
├── install.yml   # Manifest + LoadBalancer patch reference
└── README.md     # This file
```
