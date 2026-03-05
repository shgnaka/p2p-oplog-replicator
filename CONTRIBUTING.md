# Contributing Guide

## Branch Strategy

- Long-lived branch: `main` only.
- Create one short-lived branch per issue:
  - `feat/<issue-id>-<scope>`
  - `fix/<issue-id>-<scope>`
  - `chore/<issue-id>-<scope>`
  - `hotfix/<issue-id>-<scope>`
- Keep branch lifetime under 48 hours when possible.
- Use stacked PRs for dependent work; each PR must have one responsibility.

## Issue Model

We use three levels:

- Epic: top-level goal (E1 Connectivity, E2 Sync, E3 Validation/CRDT-ready)
- Capability: deliverable under an Epic
- Task: implementable unit for one PR

Every issue must include:

- Scope
- Out of scope
- Dependencies
- Acceptance criteria
- Touched paths
- Test IDs

## Pull Requests

- Link exactly one primary issue.
- Include acceptance criteria and evidence of passing tests.
- Keep PR size around 400 changed lines; split if larger.
- Rebase/update before requesting review.

## Merge Policy

- Direct pushes to `main` are prohibited.
- Merge via squash only.
- At least 1 reviewer required (security/protocol ownership review is recommended for protocol-impacting changes).
- CI must pass.
