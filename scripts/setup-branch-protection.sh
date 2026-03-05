#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   GITHUB_OWNER=owner GITHUB_REPO=repo ./scripts/setup-branch-protection.sh
# Requires:
#   gh auth login

: "${GITHUB_OWNER:?Set GITHUB_OWNER}"
: "${GITHUB_REPO:?Set GITHUB_REPO}"

repo="${GITHUB_OWNER}/${GITHUB_REPO}"

# Protect main: no direct pushes, enforce PR reviews and status checks.
tmp_json="$(mktemp)"
cat > "${tmp_json}" <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["governance"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true
}
JSON

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${repo}/branches/main/protection" \
  --input "${tmp_json}"

rm -f "${tmp_json}"

echo "Branch protection applied to ${repo}:main"
