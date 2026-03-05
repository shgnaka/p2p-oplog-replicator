#!/usr/bin/env bash
set -euo pipefail

required_files=(
  "CONTRIBUTING.md"
  "docs/multi-agent-operating-model.md"
  "docs/git-branch-strategy.md"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/ISSUE_TEMPLATE/epic.yml"
  ".github/ISSUE_TEMPLATE/capability.yml"
  ".github/ISSUE_TEMPLATE/task.yml"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing required governance file: $file"
    exit 1
  fi
done

if ! rg -qi "main.*only|only.*main" CONTRIBUTING.md; then
  echo "CONTRIBUTING.md must define that main is the only long-lived branch"
  exit 1
fi

if ! rg -q "[Ss]tacked PR" CONTRIBUTING.md docs/git-branch-strategy.md; then
  echo "Stacked PR workflow policy is missing"
  exit 1
fi

echo "Governance validation passed"
