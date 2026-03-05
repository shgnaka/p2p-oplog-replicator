# Sync Core Architecture (E2)

## Objective

Implement a deterministic signed event replication core above connectivity transport.

## Pipeline Stages

1. Ingest
- Accept `PUSH` events from connected sessions.
- Normalize envelope and attach receive metadata.

2. Verify
- Validate required envelope keys.
- Verify Ed25519 signature against member key list.

3. Dedupe
- Check `event_id` index.
- Drop exact duplicates as successful no-op.

4. Causal Order Handling
- Track Lamport clock metadata from `causal` tag.
- Buffer if dependency/ordering policy requires delay.

5. Apply
- Run deterministic reducer by `command_schema` and `merge_strategy`.
- Emit materialized state delta and applied cursor.

6. Persist
- Append event to local log and update indexes atomically.

## Failure Paths

- Invalid signature -> reject event and audit log.
- Unknown schema -> quarantine event.
- Non-deterministic reducer behavior -> hard fail and quarantine batch.

## Boundary with Connectivity

Connectivity is responsible for delivery attempts and retries only.
Sync core is responsible for validation, ordering, and state convergence.
