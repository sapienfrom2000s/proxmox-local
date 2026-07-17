# Knowledge Tracking

This folder tracks what is actually **understood**, separate from `ROADMAP.md`
(which only tracks whether a task got _done_, not whether it was understood).

## Structure

One subfolder per topic — granular by concept, not by phase, since that's how
the "questions you should be able to answer" in `ROADMAP.md` are organized.

```
knowledge/
├── ansible/
│   ├── learnings.md
│   └── examples.md
├── cgnat/
│   └── learnings.md
├── cloudflare-tunnel/
│   └── learnings.md
├── ddns/
│   └── learnings.md
├── k8s/
│   ├── learnings.md
│   ├── containerd/
│   │   └── containerd.md
│   ├── etcd/
│   │   └── etcd.md
│   ├── kube-apiserver/
│   │   └── kube-apiserver.md
│   ├── kubelet/
│   │   └── kubelet.md
│   └── networking/
│       └── pod-networking-internals.md
├── opentofu/
│   └── learnings.md
├── proxmox/
│   └── learnings.md
├── lvm/
│   └── learnings.md
└── ...
```

Each topic folder contains:

- **`learnings.md`** — dated entries of what's actually understood, in the
  user's own words, plus what caused confusion and what fixed it. This is a
  comprehension log, not copy-pasted documentation.

## Agent Instructions

When helping with a topic that already has a `knowledge/<topic>/` folder:

1. **Read it first** before explaining anything.
2. **Don't re-explain** concepts already marked as understood.
3. **Don't skip** concepts flagged as unclear or shaky.
4. Adjust depth and framing based on what's recorded in `learnings.md`.
