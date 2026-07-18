# kube-controller-manager

## Why it exists

Kubernetes is declarative. You write a Deployment with 3 replicas, and you
expect 3 replicas to exist — not 2, not 4, and not "3 but one of them is
crashing." But declarative is a promise, not a guarantee. Something has to watch
the actual state, compare it to the desired state, and fix it when they diverge.

That something is a **controller**. And kube-controller-manager is the process
that runs most of them.

Without the controller-manager, your Deployments would never create Pods. Your
Nodes would never get their addresses updated. Your Services would never have
Endpoints. The entire self-healing, self-managing behavior of Kubernetes comes
from controllers, and the controller-manager is where they live.

---

## What it is

kube-controller-manager is a **single binary** that runs multiple independent
**control loops** (controllers) inside it. Each controller watches a specific
resource type via the API server and takes action to reconcile actual state with
desired state.

It's a control-plane component, just like kube-apiserver, etcd, and
kube-scheduler. It runs as a **static Pod** on the control plane node — kubeadm
places the manifest at `/etc/kubernetes/manifests/kube-controller-manager.yaml`
and the local kubelet starts it.

The key insight: the controller-manager doesn't talk to etcd directly. It reads
from and writes to the **API server**, just like every other component. The API
server is the single point of contact with etcd.

---

## The reconciliation loop

Every controller follows the same pattern, regardless of what resource it
manages:

```
1. WATCH    →  Listen for changes to resource X via the API server
2. COMPARE  →  Desired state (spec) vs. actual state (status)
3. ACT      →  Create/update/delete objects to close the gap
4. REPEAT   →  Loop forever
```

This is the **control loop** pattern — the same pattern that drives a
thermostat, a cruise control system, or a PID controller. You don't "set and
forget." You constantly observe and correct.

```
                    ┌──────────────────────────────────┐
                    │         Controller Loop           │
                    │                                  │
  Desired State ───▶│  ┌──────────┐   ┌──────────────┐ │
  (from spec)       │  │ Compare  │──▶│ Take Action  │ │
                    │  └────▲─────┘   └──────┬───────┘ │
                    │       │                │         │
  Actual State ─────┘       └────────────────┘         │
  (from status)                                        │
                    └──────────────────────────────────┘
```

---

## The built-in controllers

The controller-manager bundles many controllers. Here are the ones that matter
most for understanding how Kubernetes works:

### Deployment controller

You create a Deployment with `replicas: 3`. The Deployment controller watches
for Deployments and their child ReplicaSets. If the Deployment spec says 3
replicas but only 2 Pods exist, it creates a new ReplicaSet (or scales an
existing one). If you scale to 5, it scales up. If you update the Deployment's
pod template, it creates a new ReplicaSet and gradually rolls out the change.

### ReplicaSet controller

A ReplicaSet's job is simpler: ensure exactly N Pods matching a selector are
running at any time. If a Pod dies (node failure, eviction, manual deletion),
the ReplicaSet controller notices and creates a replacement. This is the
self-healing mechanism — you declare "I want 3 of these" and the ReplicaSet
controller enforces it.

### Node controller

Watches for Node objects. When a Node stops reporting heartbeat (via
`/healthz`), the Node controller marks it as `NotReady` after a grace period
(40s by default). After a longer period (5 minutes), it starts tainting the node
with `node.kubernetes.io/not-ready` and evicting Pods — the response to node
failure.

### Service controller

When you create a Service of type `LoadBalancer`, the Service controller
provisions the external load balancer (in cloud environments). It talks to the
cloud provider's API (AWS ELB, GCP forwarding rule, etc.) and manages the
lifecycle of that external resource.

### EndpointSlice controller

A Service has a selector (e.g., `app: nginx`). The EndpointSlice controller
watches for Pods matching that selector and populates EndpointSlice objects with
their IP addresses and ports. This is how kube-proxy knows where to route
traffic — it reads EndpointSlices, not Services directly.

### Namespace controller

When a Namespace enters `Terminating` state, the Namespace controller starts
deleting all objects in it — Services, Deployments, ConfigMaps, Secrets, every
namespaced resource. It waits for each resource type to be fully deleted before
proceeding.

### Job controller

You create a Job that runs a Pod to completion. The Job controller watches the
Pod. If it fails, it creates a replacement. If `completions: 3` is set, it
creates new Pods until 3 succeed. This is how you run batch workloads.

### CronJob controller

A CronJob creates Jobs on a schedule. The CronJob controller checks the
`schedule` field and creates Job objects at the right times — just like cron on
a Linux box, but for Kubernetes workloads.

### GC (Garbage Collection) controller

When you delete a Deployment, the GC controller cleans up the ReplicaSets and
Pods it owns. This cascading deletion follows the `ownerReferences` field on
each object. Without it, deleting a Deployment would leave orphaned ReplicaSets
and Pods behind.

### PV (PersistentVolume) controller

Manages the lifecycle of PersistentVolumes and PersistentVolumeClaims. When a
PVC is created, the PV controller binds it to a matching PV. When a PVC is
deleted, it reclaims the PV based on the reclaim policy (Delete or Retain).

### DaemonSet controller

Ensures one Pod runs on every (or selected) node. If a new node joins the
cluster, the DaemonSet controller creates a Pod on it. If a node is removed, it
deletes the Pod. Used for node-level agents like kube-proxy, CNI plugins, and
monitoring agents.

### StatefulSet controller

Like a Deployment, but with ordered, stable identities. The StatefulSet
controller creates Pods sequentially (one at a time), gives them stable names
(`pod-0`, `pod-1`), and manages stable network identities and persistent
storage. Used for databases, message queues, and anything that needs stable
network identity.

---

## How controllers work together

The controllers aren't isolated — they form a pipeline. When you create a
Deployment, here's what happens in sequence:

```
kubectl apply -f deployment.yaml
        │
        ▼
   API Server writes Deployment to etcd
        │
        ▼
   Deployment controller notices new Deployment
        │  creates ReplicaSet
        ▼
   ReplicaSet controller notices new ReplicaSet
        │  creates Pods (with no nodeName)
        ▼
   Scheduler sees Pods without nodeName
        │  binds Pods to nodes (sets spec.nodeName)
        ▼
   Kubelet on target node sees Pods assigned to it
        │  starts containers via CRI
        ▼
   EndpointSlice controller notices new Pods
        │  updates EndpointSlice for the Service
        ▼
   kube-proxy reads EndpointSlice
        │  programs iptables/IPVS rules
        ▼
   Traffic flows to Pods
```

Each step is a different controller. No single controller knows the full story.
The Deployment controller doesn't care which node the Pods land on. The
scheduler doesn't care that the Pods came from a Deployment. The EndpointSlice
controller doesn't care about the Deployment or ReplicaSet — it only cares about
Pods matching a selector.

This **decoupled design** is a strength. Each controller is simple, focused, and
replaceable. You can swap out the scheduler without touching the Deployment
controller. You can add a custom controller that watches existing resource types
without modifying any built-in controller.

---

## The shared informer pattern

Every controller needs to watch resources via the API server. If each controller
established its own watch, the API server would be overwhelmed with duplicate
watch connections for the same resources.

The solution: **shared informers**. The controller-manager maintains a set of
informers — one per resource type. Each informer establishes a single watch
connection to the API server, caches the results locally, and notifies all
controllers interested in that resource type when something changes.

```
┌─────────────────────────────────────────────────────┐
│              kube-controller-manager                │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │            Shared Informer Factory            │  │
│  │                                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │
│  │  │ Pod      │  │ Node     │  │ ReplicaSet│    │  │
│  │  │ Informer │  │ Informer │  │ Informer  │    │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘     │  │
│  │       │              │            │           │  │
│  │       ▼              ▼            ▼           │  │
│  │  ┌──────────────────────────────────────┐     │  │
│  │  │  Local Cache (in-memory store)       │     │  │
│  │  └──────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────┘  │
│       │              │              │               │
│       ▼              ▼              ▼               │
│  Deployment    ReplicaSet    Node              ...  │
│  Controller    Controller    Controller             │
└─────────────────────────────────────────────────────┘
```

This is why you'll see `list` and `watch` operations in API server logs — the
informers first LIST all existing objects, then WATCH for changes. If a watch
connection drops, the informer re-establishes it and re-lists to catch anything
it missed.

---

## Leader election

In a multi-node control plane (3+ nodes), there are multiple instances of
kube-controller-manager running — one per control plane node. But you don't want
three controllers all trying to reconcile the same Deployments. That would cause
conflicts and duplicated work.

The solution: **leader election**. Only one instance of the controller-manager
is actively running control loops at any time. The others are on standby,
waiting to take over if the leader dies.

The mechanism:

1. Each controller-manager instance tries to acquire a **leader election lease**
   — a special resource in the `kube-node-lease` namespace
2. The instance that wins the lease becomes the **leader**
3. The leader runs all controllers
4. Other instances watch the lease; if the leader dies (lease expires), one of
   them acquires it and takes over

The lease duration is 15 seconds by default, with a 10-second retry. This means
a leader failure is detected within ~15-25 seconds, and a new leader takes over
within that window.

---

## How it runs

Like all control-plane components, kube-controller-manager runs as a **static
Pod**:

```
/etc/kubernetes/manifests/kube-controller-manager.yaml
        │
        ▼
   Kubelet watches this directory
        │
        ▼
   Starts kube-controller-manager as a static Pod
        │
        ▼
   Controller-manager connects to API server
        │
        ▼
   Starts shared informers
        │
        ▼
   Acquires leader election lease
        │
        ▼
   Runs control loops
```

### Key configuration flags

| Flag                     | Default | Notes                                       |
| ------------------------ | ------- | ------------------------------------------- |
| `--master`               | (auto)  | API server endpoint (set by kubeadm)        |
| `--leader-elect`         | true    | Enable leader election in multi-node setups |
| `--leader-elect-lease`   | 15s     | How long the leader holds the lease         |
| `--leader-elect-renew`   | 10s     | How often the leader renews                 |
| `--concurrent-*-syncs`   | varies  | Number of workers per controller type       |
| `--cluster-signing-cert` | (auto)  | CA cert for signing node/client certs       |
| `--cluster-signing-key`  | (auto)  | CA key for signing                          |
| `--kubeconfig`           | (auto)  | Path to kubeconfig for API server auth      |

The `--concurrent-*-syncs` flags control parallelism. For example,
`--concurrent-deployment-syncs=5` means 5 Deployments are reconciled in
parallel. Increasing these can help in large clusters with many resources.

---

## Authentication & Authorization

### Authentication

The controller-manager authenticates to the API server using:

- **X.509 client certificate** — signed by the cluster CA, the primary method
- **Kubeconfig** — `--kubeconfig` points to a kubeconfig file with cert-based
  credentials

In a kubeadm cluster, the certificate is at
`/etc/kubernetes/pki/controller-manager.crt`.

### Authorization

Each built-in controller runs under a specific service account with a
**ClusterRoleBinding** that grants exactly the permissions it needs. The
controller-manager doesn't use a single "controller-manager role" — each
controller has its own role.

Examples of what different controllers need:

| Controller    | Needs to read                        | Needs to write                |
| ------------- | ------------------------------------ | ----------------------------- |
| Deployment    | Deployments, ReplicaSets, Pods       | ReplicaSets, Pods             |
| ReplicaSet    | ReplicaSets, Pods                    | Pods                          |
| Node          | Nodes, Pods                          | Node status, Pods             |
| EndpointSlice | Services, Pods, Nodes                | EndpointSlices                |
| Namespace     | Namespaces, all namespaced resources | Namespaced resources (delete) |
| Job           | Jobs, Pods                           | Pods                          |

The controller-manager service account has very broad read access across the
cluster but write access is scoped per controller. This follows the principle of
least privilege — even if one controller is compromised, it can only modify the
resources it's supposed to manage.

---

## Summary

kube-controller-manager is the brain of Kubernetes self-healing. It runs
multiple controllers — each one a simple reconciliation loop that watches a
resource type and acts to converge actual state with desired state. The
Deployment controller creates ReplicaSets, the ReplicaSet controller creates
Pods, the Node controller handles node failures, the EndpointSlice controller
routes traffic. These controllers work together through the API server, using
shared informers for efficiency and leader election for HA. It runs as a static
Pod on the control plane, authenticates via client certs, and follows the same
reconciliation pattern at the heart of all Kubernetes automation.
