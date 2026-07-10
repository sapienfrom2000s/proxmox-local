# Knowledge Tracking

This folder tracks what is actually **understood**, separate from `ROADMAP.md` (which only tracks whether a task got *done*, not whether it was understood).

## Structure

One subfolder per topic — granular by concept, not by phase, since that's how the "questions you should be able to answer" in `ROADMAP.md` are organized.

```
knowledge/
├── cgnat/
│   ├── learnings.md
│   └── to-work-on.md
├── ddns/
│   ├── learnings.md
│   └── to-work-on.md
├── opentofu/
│   ├── learnings.md
│   └── to-work-on.md
├── proxmox/
│   ├── learnings.md
│   └── to-work-on.md
├── lvm/
│   ├── learnings.md
│   └── to-work-on.md
└── ...
```

Each topic folder contains exactly two files:

- **`learnings.md`** — dated entries of what's actually understood, in the user's own words, plus what caused confusion and what fixed it. This is a comprehension log, not copy-pasted documentation.
- **`to-work-on.md`** — open questions, half-formed understanding, or "should test what happens if X" items specific to that topic. Not a duplicate of `ROADMAP.md`'s task checklist — only things not already tracked there belong here.

## Agent Instructions

When helping with a topic that already has a `knowledge/<topic>/` folder:
1. **Read it first** before explaining anything.
2. **Don't re-explain** concepts already marked as understood.
3. **Don't skip** concepts flagged as unclear or shaky.
4. Adjust depth and framing based on what's recorded in `learnings.md` and `to-work-on.md`.
