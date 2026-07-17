# kube-apiserver

## Why it exists

Kubernetes has a split-brain problem by design. You have kubelet on every node
that needs to know what Pods to run. You have a scheduler that needs to know
which Pods are unscheduled. You have controller-manager that needs to know when
actual state drifts from desired state. You have etcd that holds all the data.
You have users running kubectl from their laptops. All of these need to read and
write cluster state.

If every component talked to etcd directly, you'd have a free-for-all. No place
to enforce who can do what. No place to validate that a request makes sense
before it hits the database. No single point of control. Just every component
reaching into the database with no gatekeeper.

kube-apiserver is the gatekeeper. It's the only component that touches etcd. It
sits in front of the database and runs every request through a pipeline before
allowing it through. Without it, Kubernetes is a collection of disconnected
processes with no shared state.

```
kubectl / kubelet / scheduler / controller-manager / CNI / CSI
                          │
                          v
                    kube-apiserver
                          │
                          v
                        etcd
```

---

## The request pipeline

This is the core mental model. Every request — whether it's `kubectl apply`, a
kubelet reporting Pod status, or a controller creating a replacement Pod — goes
through the same 4 stages:

```
Request
  │
  ▼
┌─────────────────┐
│ Authentication   │  "Who are you?"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Authorization    │  "Are you allowed?"
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Admission Control    │  "Should this request be allowed or modified?"
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│ etcd Storage     │  "Persist it."
└────────┬────────┘
         │
         ▼
      Response
```

If any stage rejects the request, it stops there. The request never reaches
etcd. The response goes back to the client with a clear error: 401 if you
couldn't prove who you are, 403 if you're not allowed, 403 with a message if
admission rejected it.

Think of it like a bouncer at a club. First they check your ID (authentication).
Then they check if you're on the list (authorization). Then the floor manager
decides if your outfit fits the dress code or needs a jacket (admission). Only
then do you get in (etcd).

---

## Authentication — proving who you are

The API server doesn't trust anyone by default. Every request must prove its
identity. The API server supports multiple authentication methods and checks
them in order — if one method confirms the identity, it stops checking.

### X.509 client certificates

This is the primary method. Every component that talks to the API server has a
client certificate signed by a CA the API server trusts. The TLS handshake
handles this — during the mTLS connection, both sides present certs and verify
them against the same CA.

The story of how this works is in `authentication.md`, but the short version:
kubeadm generates a CA, signs certs for kubelet, scheduler, controller-manager,
and the admin user. The admin cert lands in `~/.kube/config` when you run
`kubeadm init`. That's why kubectl works immediately — it's already got a cert
the API server trusts.

### Bootstrap tokens

The bootstrapping problem: a new worker node has no cert. The API server only
trusts certs signed by its CA. How does the worker get a cert without already
being trusted?

The bootstrap token is the answer. `kubeadm init` generates a temporary,
limited-privilege token. The worker uses this token to authenticate a
certificate signing request. The API server validates the token, signs the
worker's cert with `ca.key`, and sends it back. Now the worker has a proper
cert. The bootstrap token expires after 24 hours — it's a one-time door key.

If you need to join a node later, you generate a new token:
`kubeadm token create --print-join-command`.

### Service account tokens

Every Pod gets a service account with an auto-mounted token. When a Pod needs to
talk to the API server (like kubelet reporting status, or a controller creating
resources), it uses this token. The API server validates it against its own
signing key — this is a separate key pair from the CA, used specifically for
service account tokens.

For the full story — how the token is created, signed, injected, and why Pods
can't use certificates — see `service-account-tokens.md`.

---

## Authorization — are you allowed to do this?

Authentication tells the API server who you are. Authorization tells it what
you're allowed to do. These are separate questions — being authenticated doesn't
mean you can do everything.

### RBAC

RBAC is the only authorization mode that matters in practice. It maps subjects
(users, groups, service accounts) to permissions (verbs on resource types) via
roles and bindings.

The mental model: a **Role** is a list of permissions (like "list and watch Pods
in the monitoring namespace"). A **RoleBinding** attaches that Role to a subject
(a service account, a user, a group). The API server checks every request
against all applicable bindings.

There are two scopes:

- **Role + RoleBinding** — permissions within one namespace
- **ClusterRole + ClusterRoleBinding** — permissions across the entire cluster
  (or for non-namespaced resources like Nodes)

The key insight: RBAC is deny-by-default. If there's no binding that allows your
request, it's rejected. You must explicitly grant permissions. There's no "catch
all" rule — the absence of a binding means denial.

You can debug this with `kubectl auth can-i list pods` — it tells you exactly
whether the current user has a specific permission and which binding grants it.

Earlier modes like AlwaysAllow and ABAC were either too permissive or too hard
to configure. RBAC gives you explicit, auditable, fine-grained permissions.

**If authorization fails:** 403 Forbidden. The API server knows who you are, but
you're not allowed.

---

## Admission control — validation and mutation

After authentication and authorization, the request has passed "who are you" and
"are you allowed." But the API server isn't done. Admission controllers run
plugins that can modify the object (mutating) or reject it based on custom rules
(validating).

This is where the API server gets interesting. Authentication and authorization
are about identity and permissions. Admission is about the content of the
request itself — does this object make sense? Does it violate a policy? Should
it be modified before storage?

### Mutating admission (runs first)

These plugins can modify the object before it's stored. You don't see the
modification in your kubectl output — the API server applies it silently.

Real examples:

- You create a Pod without specifying a service account. Mutating admission
  auto-injects the default service account token.
- You create a Pod without resource limits. LimitRanger injects default limits
  from the namespace's LimitRange.
- You create a Deployment with no storage class specified. DefaultStorageClass
  adds the default one.
- Istio uses a mutating webhook to inject a sidecar container into every Pod in
  the mesh.

The pattern: the API server calls an external service (a webhook), sends it the
object, the service returns a modified version, and the API server stores that
instead. This is how service meshes, policy engines, and custom tooling extend
the API server without modifying it.

### Validating admission (runs after mutation)

These plugins can only reject — they can't modify the object. They check the
final object (after mutations) against rules.

Real examples:

- NamespaceLifecycle rejects creation of objects in a namespace that's being
  terminated.
- ResourceQuota rejects a Pod that would push the namespace over its CPU or
  memory quota.
- A validating webhook calls OPA/Gatekeeper to check if the object violates a
  custom policy (like "no containers running as root").

The two-phase design matters: mutating runs first so that all modifications are
done before validation checks the final object. If validation ran first, a
mutating webhook could modify the object into something that violates the policy
after validation already approved it.

**If admission rejects:** 403 Forbidden with a message explaining why. The
object is never written to etcd.

---

## How it runs

kube-apiserver runs as a **static Pod** on the control plane node. kubeadm
places the manifest at `/etc/kubernetes/manifests/kube-apiserver.yaml`, and the
local kubelet picks it up and starts it — the same pattern used for etcd,
scheduler, and controller-manager.

The important configuration points:

- **`--etcd-servers`** — where to find etcd (localhost on the control plane
  node)
- **`--service-cluster-ip-range`** — the virtual IP range for Services.
  ClusterIPs come from this pool. These IPs don't exist on any network interface
  — they're pure kube-proxy magic.
- **`--advertise-address`** — the IP other components use to reach this API
  server
- **`--secure-port`** — 6443, the standard entry point

### The certs it needs

- **CA cert and key** (`ca.crt`, `ca.key`) — the root of trust, used to sign and
  verify client certificates
- **API server cert** (`apiserver.crt`) — served to clients connecting on 6443,
  signed by the CA. SANs include the node IP, node name, `kubernetes`,
  `kubernetes.default`, and `kubernetes.default.svc`
- **Service account key pair** (`sa.key`, `sa.pub`) — signs and verifies service
  account tokens, separate from the CA
- **Client CA** — the CA used to verify client certificates during mTLS

The API server cert is what kubelet, kubectl, and every other client validate
when they connect. The client CA is what the API server uses to verify incoming
connections. Together, they form the mTLS trust chain.

---

## Health and observability

The API server exposes health endpoints that matter for understanding whether
it's actually functioning:

- **`/livez`** — is the process alive? Checks internal health: etcd connection,
  certificate validity, initialization state. If this fails, the API server
  should be restarted.
- **`/readyz`** — is it ready to serve traffic? During startup, the API server
  loads caches and establishes connections. It's alive but not ready yet. Once
  caches are warm, it becomes ready.
- **`/metrics`** — Prometheus-format metrics. Shows request latency, error
  rates, watch counts, etcd request durations.
- **`/healthz`** — legacy endpoint that combines liveness and readiness.

The separation between liveness and readiness matters. An API server can be
alive (not deadlocked, etcd is reachable) but not ready (still loading caches,
not yet serving requests). If you put only a liveness check on the API server,
it might accept traffic before it's actually ready to handle it.

`kubectl get --raw /livez?verbose` gives you a breakdown of every individual
check and whether it passed.

---

## Key numbers

| Parameter              | Default | Notes                                         |
| ---------------------- | ------- | --------------------------------------------- |
| Secure port            | 6443    | HTTPS, the standard entry point               |
| Max requests in flight | 400     | Non-mutating requests (reads)                 |
| Max mutating requests  | 200     | Mutating requests (writes) — throttled harder |
| Watch cache size       | 100     | Cached watch events per resource type         |
| Event TTL              | 1 hour  | How long events persist before auto-deletion  |
| Request timeout        | 300s    | Hard timeout for any single API request       |

The two throttling limits matter in practice. Reads (GET, LIST, WATCH) share a
pool of 400 concurrent requests. Writes (CREATE, UPDATE, DELETE) share a
separate pool of 200. This means a burst of LIST requests won't starve writes,
and a burst of writes won't starve reads. If you see `429 Too Many Requests`
errors, you've hit these limits — usually during a large-scale operation or a
misbehaving controller that's LISTing too frequently.

---

## Summary

kube-apiserver is the front door to the cluster. Every component talks through
it. The request pipeline — authentication, authorization, admission, etcd — is
the core mental model. Authentication proves identity via mTLS certs, bootstrap
tokens, service account tokens, or OIDC. Authorization checks permissions via
RBAC. Admission validates and mutates objects before storage. The API server
runs as a static Pod on the control plane, serves HTTPS on 6443, and is the only
component that touches etcd. Understanding this pipeline is understanding how
Kubernetes actually works.
