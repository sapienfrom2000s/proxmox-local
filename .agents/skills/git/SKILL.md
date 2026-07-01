---
name: git-expert
description: Use when committing changes, managing branches, resolving merge conflicts, staging files, rebasing, or writing git commit messages.
---

# Git Expert Skill

This skill guides the agent in managing version control tasks cleanly and effectively.

## When to use this skill

- Staging, committing, pushing, or pulling changes in git.
- Handling branch creation, merging, or rebasing.
- Resolving complex merge conflicts.
- Writing clear, conventional, and meaningful git commit messages.

## Best Practices & Guidelines

### 1. Commit Messages
- Follow **Conventional Commits** formatting where appropriate (e.g., `feat: add ...`, `fix: resolve ...`, `docs: update ...`).
- Use the imperative mood in the subject line (e.g., "add feature" instead of "added feature" or "adds feature").
- Limit the subject line to 50 characters, and separate it from the body with a blank line.

### 2. Branching & Merging
- Keep branch names descriptive and structured (e.g., `feature/login-page`, `bugfix/memory-leak`).
- Regularly fetch and rebase your feature branches against the main branch to reduce merge conflicts.
- Avoid using force-pushes (`git push --force`) on shared main/production branches; use `--force-with-lease` if force-pushing on your personal feature branch is necessary.

### 3. Staging and Diffs
- Always run `git status` and review `git diff` before staging (`git add`) and committing to prevent unintended files from being tracked.
- Use `.gitignore` to exclude OS-specific files (e.g., `.DS_Store`), IDE settings, and build artifacts.
