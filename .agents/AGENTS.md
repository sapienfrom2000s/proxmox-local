# Project Rules & Workspace Context

## Project

Building a production-style platform engineering homelab on a **single physical HP Mini PC** running **Proxmox VE**, with **Debian 13** as the base OS for all VMs.

The goal is to simulate real cloud infrastructure patterns — network isolation (public/private subnet split), Infrastructure as Code, GitOps, observability, and chaos resiliency testing — entirely on this one box, provisioned through code rather than manual UI clicks.

This starts as a single-node build. More physical nodes may be added later once this setup is validated. **Before doing anything, check `ROADMAP.md` for current progress** — don't assume the user is at Phase 1; the checklist there is the source of truth for what's actually done. Detailed technical documentation of completed steps must be maintained and updated in [WHAT_IS_DONE.md](file:///Users/thirtyone/repos/proxmox-local/WHAT_IS_DONE.md) as progress is made.

## Knowledge tracking

The `knowledge/` folder tracks what the user actually understands, separate from `ROADMAP.md` (which only tracks whether a task got *done*, not whether it was understood).

Structure: one subfolder per topic (e.g. `knowledge/opentofu-proxmox/`, `knowledge/cilium-cni/`, `knowledge/argocd/`) — granular by concept, not by phase, since that's how the "questions you should be able to answer" in `ROADMAP.md` are actually organized. Each topic folder contains two files:

- **`learnings.md`** — dated entries of what's actually understood, in the user's own words, plus what caused confusion and what fixed it. This is a comprehension log, not copy-pasted documentation.
- **`to-work-on.md`** — open questions, half-formed understanding, or "should test what happens if X" items specific to that topic. This is not a duplicate of `ROADMAP.md`'s task checklist — only things not already tracked there belong here.

When helping with a topic that already has a `knowledge/<topic>/` folder, read it first. Adjust explanations based on what's already marked understood vs. still shaky — don't re-explain settled concepts, and don't skip past ones flagged as unclear.

## Ignore Files
- **`POST_STEP_CHECKLIST.md`**: Do not read, modify, or reference this file. It is reserved for manual user verification of conceptual understanding.

## Diagram Rules
- **Use ASCII Diagrams**: Always use ASCII art/diagrams instead of Mermaid for visual representation.

## Documentation Checks
- **Core Document Synchronization**: Whenever any change is made, proactively check if you need to update/modify:
  - `AGENTS.md` (rules and context)
  - `README.md` (high-level introduction and architecture diagrams)
  - `ROADMAP.md` (milestone checklist status)
  - `WHAT_IS_DONE.md` (technical details of implemented progress)

