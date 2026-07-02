# Project Rules & Workspace Context

## Project

Building a production-style platform engineering homelab on a **single physical HP Mini PC** running **Proxmox VE**, with **Debian 13** as the base OS for all VMs.

The goal is to simulate real cloud infrastructure patterns — network isolation (public/private subnet split), Infrastructure as Code, GitOps, observability, and chaos resiliency testing — entirely on this one box, provisioned through code rather than manual UI clicks.

This starts as a single-node build. More physical nodes may be added later once this setup is validated. **Before doing anything, check `ROADMAP.md` for current progress** — don't assume the user is at Phase 1; the checklist there is the source of truth for what's actually done. Detailed technical documentation of completed steps must be maintained and updated in [WHAT_IS_DONE.md](file:///Users/thirtyone/repos/proxmox-local/WHAT_IS_DONE.md) as progress is made.

## Knowledge tracking

See [`knowledge/README.md`](file:///Users/thirtyone/repos/proxmox-local/knowledge/README.md) for the full knowledge system rules and structure.

**Rule**: When helping with a topic that has a `knowledge/<topic>/` folder, read `learnings.md` and `to-work-on.md` first before explaining anything.

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

