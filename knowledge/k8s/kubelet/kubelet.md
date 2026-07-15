# Kubelet

## Why Kubelet Exists

Kubernetes is a declarative system. You tell the API server *what* you want — "run 3 replicas of nginx" — and something has to make that happen on actual machines. The API server stores the desired state in etcd, the scheduler picks which node runs what, but **nothing actually runs containers until kubelet does it**.

Kubelet is the node-level agent. It exists on every node — control plane and workers. It's the bridge between the desired state in etcd and the actual containers running on a node. Without it, Pod specs are just YAML files.

## What Kubelet Does

At its core, kubelet is a reconciliation loop:

1. Watches the API server for Pods assigned to its node (`spec.nodeName == <self>`)
2. Compares desired state (Pod spec) vs actual state (running containers)
3. Starts, stops, or restarts containers to converge the two
4. Reports status back to the API server

Beyond that, kubelet handles:
- **Liveness/readiness/startup probes** — runs health checks and reports results
- **Volume mounts** — coordinates with CSI drivers to attach storage
- **Resource enforcement** — applies cgroup limits (CPU, memory) from Pod requests/limits
- **Log collection** — exposes container logs via the API server
- **Eviction** — kills Pods when node resources are under pressure (disk, memory, PID)

## Communication with the API Server

Kubelet establishes a **watch connection** to the API server — a single long-lived HTTP request that streams events (`ADDED`, `MODIFIED`, `DELETED`) in real-time. No polling.

The watch returns all Pods, but kubelet client-side filters for `spec.nodeName == <self>`. When a Pod is deleted or updated, the API server pushes the change, and kubelet reacts immediately. This is the same watch mechanism used by controllers, schedulers, and every other Kubernetes component.

## Authentication & Authorization

Kubelet authenticates to the API server using one of:

- **X.509 client certificate** — most common in production. Kubelet presents a cert signed by the cluster CA.
- **Bootstrap token** — used during initial node registration. Kubelet uses a temporary token to get a proper certificate.
- **Service account token** — less common for kubelet itself.

On the API server side, kubelet is authorized via **Node Authorizer** — a special authorizer that only allows kubelet to read Nodes and Pod status, write Pod/node status and events, and read Services/Endpoints.

Kubelet also has its own **authorization mode** for incoming requests (from the API server or `kubectl exec`): `AlwaysAllow`, `AlwaysDeny`, or `Webhook` (delegates to SubjectAccessReview). This controls who can exec into containers or read logs on this node.

## Port 10250 — The Kubelet API

Kubelet exposes an HTTPS API on port **10250**. This is the kubelet API — not the Kubernetes API server.

What it serves:
- `/pods` — list of Pods on the node
- `/run`, `/exec`, `/attach` — proxy for `kubectl exec`, `kubectl attach`
- `/logs` — container log access
- `/metrics` — kubelet and container metrics
- `/configz` — current kubelet configuration
- `/healthz` — health endpoint

Who calls it:
- **API server** — proxies `kubectl exec`, `kubectl logs`, etc. through kubelet on this port
- **kubeletctl** — security scanning tool
- **Metrics server** — scrapes `/metrics`

The API server connects to kubelet here for operations like exec, attach, port-forward, and logs. This is why proper auth matters — anyone with access to 10250 can exec into containers on that node.

## Static Pods

Kubelet can manage Pods **without** the API server. These are called **static Pods**:

- Defined as YAML files in a directory (usually `/etc/kubernetes/manifests/`)
- Kubelet watches that directory and creates/stops containers directly
- A mirror Pod is created in the API server for visibility, but kubelet owns the lifecycle

This is how the control plane itself runs on the control plane node — API server, etcd, scheduler, controller manager are all static Pods managed by kubelet. `kubeadm` places manifests in `/etc/kubernetes/manifests/`, kubelet picks them up, and the control plane boots.

## CRI — Container Runtime Interface

Kubelet doesn't directly manage containers. It talks to a **container runtime** via the **CRI (Container Runtime Interface)** — a gRPC API defined by Kubernetes.

The flow:
```
kubelet → CRI gRPC → containerd → runc (OCI runtime) → container
```

CRI defines two services:
- **ImageService** — pull, list, remove images
- **RuntimeService** — create, start, stop, remove containers; run PodSandbox (pause containers)

Kubelet doesn't care what the runtime is underneath — it just speaks CRI. Containerd implements this interface, but kubelet is runtime-agnostic.

### crictl vs ctr vs nerdctl

Three tools, three different things:

- **crictl** — talks to the **CRI gRPC** endpoint. This is the "kubelet's view." `crictl pods` shows exactly the Pods kubelet knows about. **This is the right tool for debugging kubelet issues.**
- **ctr** — talks to containerd's **native API**. Lower level, shows everything containerd knows including things not exposed via CRI. Useful for deep containerd debugging but not what kubelet uses.
- **nerdctl** — Docker-compatible CLI for containerd's **native API**. Supports `docker-compose`, build, etc. Great for developers, irrelevant for kubelet debugging.

### kubeletctl

`kubeletctl` is a security auditing tool, not a container tool. It connects to kubelet's API on port 10250 and can:
- List pods, execute commands in containers, read logs
- Scan for security misconfigurations (anonymous auth, readonly port)
- Test kubelet access permissions

It's a pentesting/debugging tool — it talks to the kubelet API, not the container runtime.

## Kubelet's Two API Surfaces

1. **CRI API (gRPC, internal)** — kubelet as a **client**, talking to the container runtime. Kubelet calls `RunPodSandbox`, `CreateContainer`, `StartContainer`, etc.
2. **Kubelet HTTPS API (port 10250)** — kubelet as a **server**, serving requests from the API server and tools like kubeletctl. Handles `/pods`, `/exec`, `/logs`, `/metrics`.

The CRI API is internal to the node. The HTTPS API is network-accessible and requires authentication.

## Summary

Kubelet is the node-level agent that makes Kubernetes actually work. It watches for Pods assigned to its node, turns Pod specs into running containers via the CRI, monitors them, heals them, and reports status back. It's the enforcer of the reconciliation loop at the node level — the piece that turns declarative YAML into real processes.
