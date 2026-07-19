# How Authentication Works in Kubernetes

## The problem

Kubernetes is a bunch of components talking to each other over a network.
kubelet talks to the API server. The API server talks to etcd. Controllers talk
to the API server. If an attacker sits on your network, they can pretend to be
any of these components. You need a way to prove identity on both sides of every
connection.

## The solution: mTLS

Every connection uses mutual TLS. Both sides present a cert, both sides verify
it against a shared CA. If the cert isn't signed by the CA, the connection is
rejected. No cert, no talk.

## Where the CA comes from

The CA is a key pair — a root cert (`ca.crt`) and a private key (`ca.key`). The
root cert is public, shared with everyone. The private key is secret, held only
by whoever issues certs.

- **Self-signed (kubeadm default):** `kubeadm init` generates its own CA. The
  cluster is its own authority. Nobody external needs to trust it.
- **Proper CA (production):** You bring your organization's CA. The Kubernetes
  certs are signed by the same CA that signs everything else in your
  infrastructure. External systems already trust it.

The difference: with a self-signed CA, trust exists only within the cluster.
With a proper CA, trust extends beyond the cluster to anything that already
trusts your org's root.

## How a worker node joins

This is where the bootstrap token comes in. The problem: the new worker has no
cert. The API server only trusts certs signed by the CA. How does the worker get
a cert without already having one?

Step by step:

1. `kubeadm init` on the control plane generates the CA and a bootstrap token —
   a temporary, limited-privilege credential printed in the join command
2. On the worker, you run `kubeadm join` with that token
3. The worker generates a key pair locally (public + private)
4. The worker sends a CSR (Certificate Signing Request) — just its public key —
   to the API server, authenticated with the bootstrap token
5. The API server validates the token. If it's valid and not expired, it signs
   the CSR with `ca.key`, producing a cert
6. The API server sends the signed cert back to the worker
7. The worker saves the cert. From now on, it uses this cert for every
   connection

The bootstrap token is the proof of identity. Only someone who has it can get a
cert signed. That's why it's short-lived (24 hours), limited in scope (can only
request certs), and you're expected to use it immediately and forget it.

If you forget the token or it expires, you generate a new one:

```bash
kubeadm token create --print-join-command
```

## How mTLS actually works in practice

Once every component has its cert, every connection works like this:

**Kubelet → API server:**

- Kubelet presents its cert (signed by the CA)
- API server verifies: "Is this cert signed by my CA?" Checks against `ca.crt`
- If yes, the connection proceeds. If no, rejected.

**API server → kubelet** (for `kubectl exec`, `kubectl logs`):

- API server presents its cert (signed by the CA)
- Kubelet verifies: "Is this cert signed by my CA?" Checks against `ca.crt`
- Same thing, other direction.

**API server → etcd:**

- API server presents its client cert (signed by the CA)
- etcd verifies against its own `ca.crt`
- Also mTLS, same pattern.

Neither side uses `ca.key` during the handshake. The key is only used when
_issuing_ certs. During the connection, both sides just verify against `ca.crt`.

## Why only the control plane has ca.key

Because only the control plane signs certs. When a worker joins, the API server
signs the worker's cert. The worker never needs to sign anything — it only needs
`ca.crt` to verify the API server's identity. Giving workers `ca.key` would mean
any compromised worker could sign certs for any identity. That defeats the whole
purpose.

## Self-signed vs proper CA — same story, different root

Everything above works identically in both cases. The only difference is where
the root cert comes from:

**Self-signed:** kubeadm generates `ca.crt` and `ca.key`. The trust chain is:

```
kubelet cert → kubeadm CA → done (self-signed root)
```

**Proper CA:** your org's CA signs the Kubernetes CA or the certs directly. The
trust chain is:

```
kubelet cert → Kubernetes CA → org CA → org root (already trusted by your infra)
```

With a proper CA, if a node is compromised, you revoke its cert through your
org's CRL/OCSP — same process as revoking any other cert. With a self-signed CA,
revocation is your problem. With a proper CA, external systems (monitoring,
CI/CD, service mesh) already trust the chain without you distributing `ca.crt`
everywhere.

## See also

- [networking/external-https.md](../networking/external-https.md) — external
  HTTPS flow (browser → TLS terminator → pod, separate CA for external trust)
