# Sync Conformance Tests (A-D)

Minimum: 12 cases (3 per group).

## Group A: Signature and Envelope Validation

- A-01: valid signature accepted
- A-02: invalid signature rejected with `ERR_SIG_INVALID`
- A-03: missing required field rejected

## Group B: Idempotency and Integrity

- B-01: duplicate `event_id` accepted as no-op
- B-02: `event_id` collision with different hash quarantined
- B-03: replay burst keeps stable state

## Group C: Ordering and LWW/Tombstone

- C-01: out-of-order events converge via tuple rule
- C-02: lamport tie resolves by `author` lexical order
- C-03: tombstoned entity does not reappear from stale replay

## Group D: Partition/Rejoin Recovery

- D-01: split-brain + heal converges to same final state
- D-02: missing range requested via cursor and reconciled
- D-03: quarantine events remain isolated during re-materialization

## Evidence Format

For each case capture:
- `test_id`
- `input_event_sequence`
- `expected_final_hash`
- `actual_final_hash`
- `result`
