# CRDT Migration Verification Plan

## Primary Metrics

- `conversion_rate` = converted_events / total_events
- `quarantine_rate` = quarantined_events / total_events
- `state_divergence_rate` = divergent_nodes / total_nodes

## Quality Gates

- `state_divergence_rate` must be `0.0` for mandatory scenarios.
- `conversion_rate` must be above threshold declared per scenario.
- Quarantine records must contain valid reason codes and snapshots.

## Mandatory Scenarios

- `MIG-01`: baseline conversion with valid event stream.
- `MIG-02`: mixed convertible/non-convertible events.
- `MIG-03`: partition + rejoin during migration run.

## Failure Policy

- If any mandatory scenario diverges, migration candidate is rejected.
- Unknown quarantine reason codes fail the run.
