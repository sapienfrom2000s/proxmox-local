### MVCC (Multi-Version Concurrency Control)

Every write to etcd creates a new **revision**. Old values aren't overwritten —
they're kept alongside the new one. This is how watches work: a client says
"give me everything after revision 4721" and gets a stream of changes.

This also means etcd can serve **historical reads** — you can ask for the state
at a specific revision. Kubernetes doesn't use this directly, but it's what
makes watches efficient and crash-recoverable. When a controller reconnects
after a network blip, it just resumes from the last revision it saw — no data
loss, no full resync.

The tradeoff: old revisions accumulate and waste disk. etcd runs periodic
**compaction** (removes old revisions) and **defragmentation** (reclaims disk)
to manage this.

### Lease-based keys

Some keys in etcd are attached to a **lease** — a TTL that auto-deletes the key
when the lease expires. Kubernetes uses this for:

- **Node heartbeats**: kubelet periodically refreshes its Node lease. If a node
  stops heartbeating, its lease expires, the node is marked NotReady, and Pods
  are evicted after `pod-eviction-timeout`.
- **Lease-based leader election**: controller candidates create a key with a
  short lease. Only the leader can refresh it. When the leader dies, the key
  expires, and another candidate wins.

Without leases, etcd would accumulate dead-node records and stale leadership
keys forever.

---

## etcd operations you'll actually do

### Backup and restore

This is the most important operational skill for etcd. Backups are the only
safety net for data loss or corruption.

**Taking a snapshot:**

```bash
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot-$(date +%Y%m%d).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

**Verifying a snapshot:**

```bash
ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-snapshot-20250715.db --write-out=table
```

Shows: hash, revision, total keys, total size. If this looks sane, the backup is
usable.

**Restoring (disaster recovery):**

```bash
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot-20250715.db \
  --data-dir=/var/lib/etcd-restore \
  --name=<etcd-member-name> \
  --initial-cluster=<etcd-member-name>=https://<node-ip>:2380 \
  --initial-advertise-peer-urls=https://<node-ip>:2380
```

Then swap the data dir and restart etcd. The restore replaces whatever etcd has
with the snapshot state.

**When to back up:** Before any kubeadm upgrade, before etcd compaction, and
periodically (cron job). Backups are cheap — a homelab snapshot is typically a
few MB.

### Checking cluster health

```bash
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

```bash
ETCDCTL_API=3 etcdctl endpoint status \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  --write-out=table
```

The status output shows: endpoint, DB size, leader, raft term, applied index.
Watch for DB size growth (should stay under 2 GB default) and whether the leader
is stable.

### Compaction and defragmentation

etcd keeps old revisions. Over time, the DB grows. If it approaches the 2 GB
limit:

```bash
# Compact to the latest revision
ETCDCTL_API=3 etcdctl compact $(ETCDCTL_API=3 etcdctl endpoint status \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  --write-out=json | jq -r '.status.header.revision') \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

```bash
# Defragment to reclaim disk
ETCDCTL_API=3 etcdctl defrag \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

**Compaction** removes old revisions. **Defragmentation** reclaims the disk
space. Both cause a brief pause — defragmentation is especially heavy. Don't do
this in production during traffic spikes.

### Moving etcd off the control plane node

For larger clusters, you can run etcd on dedicated machines (external etcd). The
API server connects to the external etcd cluster instead of the local one. This
separates the failure domains — a control plane failure doesn't take down the
data store.

In practice, this is overkill for a homelab. It's mentioned because you'll see
it referenced in kubeadm docs and Kubernetes certifications.
