# Git Branch Strategy

## Core Model

- Trunk-based development with short-lived branches.
- `main` is the only long-lived branch.
- Use stacked PRs for dependent changes.

## Naming

- `feat/<issue-id>-<scope>`
- `fix/<issue-id>-<scope>`
- `chore/<issue-id>-<scope>`
- `hotfix/<issue-id>-<scope>`

Example: `feat/42-sync-lww-apply`

## Stacked PR Workflow

1. Open `PR-1` for shared foundations.
2. Open `PR-2` based on `PR-1`.
3. Open `PR-3` based on `PR-2`.
4. After lower PR merges, rebase upper PRs onto `main`.

## Merge Gates

- 1 approval minimum.
- One approval must come from protocol/security ownership.
- CI required.
- Squash merge only.

## Release Tagging

- Epic completion tags: `release/YYYYMMDD-<epic>`
- Protocol version tags: `protocol-vX`
