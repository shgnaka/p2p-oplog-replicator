# E3 Validation Harness Architecture

## Goal

Provide repeatable validation for connectivity, sync convergence, and migration safety.

## Harness Components

- `scenario-loader`
  - Loads scenario definitions for LAN/public/NAT and partition/rejoin patterns.
- `node-orchestrator`
  - Boots N nodes with deterministic seed and network profile.
- `event-injector`
  - Replays event sequences and fault patterns (duplication, reorder, delay).
- `collector`
  - Collects per-node state hash, apply logs, and failure categories.
- `reporter`
  - Produces normalized JSON reports for CI and manual review.

## Execution Flow

1. Load scenario and seed.
2. Start nodes and apply network profile.
3. Inject events/faults for fixed duration.
4. Collect final state and logs.
5. Evaluate assertions and emit report.

## Required Outputs

- `scenario_id`
- `seed`
- `node_count`
- `success`
- `assertions[]`
- `final_state_hash_by_node`
- `quarantine_count`
- `failure_breakdown`

## Determinism Policy

- Scenario seed must be fixed per run.
- Any non-deterministic behavior must be reported with seed and replay recipe.
