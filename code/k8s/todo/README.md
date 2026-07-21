# Todo API

Flask REST API backed by Redis. Deployed to Kubernetes via ArgoCD.

## Architecture

```
                          ╭──────────────────────────────────────────────╮
                          │              Kubernetes Cluster              │
                          │                                              │
  ╭────────╮   ╭────────╮ │ ╭────────────╮                               │
  │        │──▶│MetalLB │─┼▶│ Flask API  │                               │
  │  User  │   │   LB   │ │ │  Service   │                               │
  │        │◀──│        │◀┼─│ (LoadBal)  │                               │
  ╰────────╯   ╰────────╯ │ ╰─────┬──────╯                               │
                          │       │                                      │
                          │       ▼                                      │
                          │ ╭────────────╮   ╭───────────╮               │
                          │ │ Flask API  │──▶│   Redis   │               │
                          │ │    Pod     │   │  Service  │               │
                          │ ╰────────────╯   │(ClusterIP)│               │
                          │                  ╰─────┬─────╯               │
                          │                        │                     │
                          │                        ▼                     │
                          │                  ╭───────────╮               │
                          │                  │   Redis   │               │
                          │                  │    Pod    │               │
                          │                  ╰───────────╯               │
                          ╰──────────────────────────────────────────────╯

        ╭──────────╮   ╭──────────╮
        │  GitHub  │◀─▶│  ArgoCD  │   GitOps: git push = deploy
        │   Repo   │   ╰──────────╯
        ╰──────────╯
```
