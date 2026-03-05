# CI Artifact Contract for Sync/Migration

## Artifact Set

Each validation run must publish:
- `summary.json`
- `scenario-results.jsonl`
- `quarantine-records.jsonl`
- `node-state-hashes.json`

## summary.json fields

- `run_id`
- `git_sha`
- `suite`
- `total_scenarios`
- `passed_scenarios`
- `failed_scenarios`
- `conversion_rate`
- `quarantine_rate`

## Retention

- Keep artifacts for at least 30 days.
- Keep artifacts for all failed runs until issue closure.

## Regression Rule

A PR fails if:
- any mandatory scenario fails, or
- conversion rate regresses beyond configured threshold, or
- required artifact files are missing.
