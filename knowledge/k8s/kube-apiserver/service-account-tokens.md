# Service Account Tokens

## Why Pods can't use certificates

Kubelet uses a client certificate because it authenticates during the TLS
handshake — before any HTTP traffic. Both sides present certs, both sides verify
each other. The connection is either accepted or rejected at the transport
layer.

Pods don't work that way. A Pod is already inside the cluster, running on a node
that's already authenticated. The network is already trusted. The Pod doesn't
need to prove "I am a legitimate member of this cluster" — the node already
proved that. The Pod needs to prove "I am cert-manager in the monitoring
namespace, and I'm allowed to list certificates."

That's an application-layer question, not a transport-layer question.
Certificates operate at TLS level. Tokens operate at HTTP level. The Pod's
identity is conveyed in the `Authorization: Bearer <token>` header, after the
TLS handshake has already completed.

If you used a client certificate for Pods, you'd be solving the wrong problem.
You'd be authenticating at the transport layer when what you really need is
scoped, per-workload identity at the application layer. A certificate proves
"this is a member of the cluster." A token proves "this is cert-manager, in this
namespace, with these permissions." Different questions, different mechanisms.

## What a service account token is

A credential that proves a Pod's identity to the API server. When a Pod needs to
talk to the API server — to list resources, create objects, update status — it
needs to authenticate. It can't use kubectl, it can't use a client certificate.
It uses a service account token — a JWT that says "I am this service account in
this namespace."

## What a service account is

An identity. Every namespace has a `default` service account. You can create
custom ones — one for cert-manager, one for your operator, one for Prometheus.
Each is just a name in a namespace, a record the API server knows about.

An identity without a credential is useless. The service account is a name in a
database. The token is the credential — the thing the Pod shows to the API
server to prove which service account it's running as.

## How the token gets created

When you submit a Pod to the API server, the request goes through the pipeline.
One of the mutating admission controllers is the `ServiceAccount` controller. It
runs before the Pod is stored in etcd.

It checks two things: did you specify a service account? If not, it fills in
`default`. Did you set `automountServiceAccountToken` to `false`? If not, it
assumes you need a token.

Then it modifies the Pod spec — adds a projected volume pointing to the API
server's token endpoint. This modified spec is what gets written to etcd. You
never see the change in your YAML.

## How the token is signed

The API server has its own key pair — `sa.key` and `sa.pub` — separate from the
CA. When the admission controller decides the Pod needs a token, the API server
generates a JWT containing the service account name, namespace, UID, and expiry.
It signs the JWT with `sa.key`. That signature is what makes the token valid.
Without the private key, nobody can forge one.

## How the token reaches the container

Kubelet picks up the Pod spec, sees the projected volume, and mounts it into the
container at `/var/run/secrets/kubernetes.io/serviceaccount/`. Three files
appear: `token` (the JWT), `ca.crt` (the cluster CA cert), and `namespace`.

## How the Pod talks to the API server

The container reads the token file. But first — the TLS handshake. The API
server presents its server cert — the cert it generated during `kubeadm init`,
signed by the cluster CA. The Pod verifies this server cert against `ca.crt` —
the same cluster CA cert mounted into the container. The Pod uses this CA to
confirm it's talking to the real API server, not an imposter. Connection
established. One-sided — the server proved its identity, the Pod did not.

Then the Pod sends the HTTP request with the token in the
`Authorization: Bearer <token>` header. The API server sees the token, verifies
the JWT signature against `sa.pub`, knows which service account it belongs to,
and runs RBAC.

This is the fundamental difference from nodes. Nodes authenticate at the
transport layer — mTLS, both sides present certs, before any HTTP traffic. Pods
authenticate at the application layer — way TLS, then a Bearer token. Weaker,
but appropriate for workloads that are already inside a trusted network.

## What permissions the token has

The token itself is just an identity card. It has no permissions baked in. When
the API server receives the request, it verifies the JWT signature, looks up the
service account, then checks RBAC to see if that service account is allowed to
do what it's asking. If no RoleBinding exists for this service account, the
request is denied. Deny-by-default — the absence of a binding means no
permission.

## Why this matters for security

If a container is compromised, the attacker gets the service account token. The
damage is limited by what that service account is allowed to do. If it's the
`default` account with no bindings, the attacker can't do much. If it's a
service account with broad permissions, the attacker can read Secrets, create
Pods, pivot laterally.

That's why you create dedicated service accounts with minimal RBAC per workload,
and disable token auto-mounting when a Pod doesn't need API server access.
