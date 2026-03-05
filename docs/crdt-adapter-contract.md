# CRDT Adapter Contract (lww_v1 -> crdt_x_v1)

## Input

Adapter input record:
- `event` (validated LWW envelope)
- `materialized_before` (optional)
- `adapter_version`

## Output

Adapter returns exactly one result:
- `APPLY`: emits converted CRDT op(s)
- `QUARANTINE`: emits reason and supporting metadata

## Determinism Requirements

- Same input must always produce identical output.
- No clock/time/random dependency allowed.
- Conversion must be pure and side-effect free.

## Quarantine Reasons

- `Q_UNSUPPORTED_SCHEMA`
- `Q_NON_CONVERTIBLE_COMMAND`
- `Q_INTEGRITY_MISMATCH`
- `Q_VERSION_UNSUPPORTED`

## Auditability

Each adapter decision must include:
- `event_id`
- `adapter_version`
- `decision`
- `reason_code` (if quarantined)
- `explain` (short human-readable message)
