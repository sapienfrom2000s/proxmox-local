---
name: linear
description: Use when creating or updating Linear issues, tickets, or tasks for this project.
---

# Linear Issue Management

This skill guides the agent in creating well-structured Linear tickets for the Proxmox Local project.

## When to use this skill

- Creating new Linear issues/tickets related to the project.
- Updating existing Linear ticket with details, sections, or corrections.

## Issue Template

Every Linear ticket must follow this structure:

### What

Concise description of what needs to be done. Break into sub-steps if multiple.

### Why

Rationale — what problem this solves, why it exists, what happens if skipped.

### Request/Response Flow

ASCII diagram showing data/request/state flow if applicable (see Diagram Rules in AGENTS.md).

### Must know before implementing

Key concepts the implementer needs to understand before touching this. Cover terminology, failure modes, edge cases, and common misconceptions.

### Glossary

Domain-specific terms defined (pveum, LVM, thin provisioning, VirtIO, etc.)

## Rules

- Always include all sections from the template above.
- "Depends on" is NOT part of the template — do not add it.
- When answering questions about a topic that has related tickets, reference the ticket ID and link.
- When creating tickets, check ROADMAP.md first to understand current phase/progress.
