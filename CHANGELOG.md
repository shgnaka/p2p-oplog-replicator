# Changelog

## 2026-03-05 - release/20260305-implementation

### Added
- Connectivity implementation:
  - discovery abstraction and candidate lifecycle state machine
  - dial scheduler retry policy and session manager events
  - protocol message codec + transport bridge
- Sync implementation:
  - event envelope validation and Ed25519 signature verification
  - append-only event log and event_id idempotency index
  - deterministic LWW+tombstone reducer and materialized view store
- Validation/Migration implementation:
  - deterministic multi-node scenario runner and report writer
  - lww_v1 -> crdt_x_v1 adapter runtime and quarantine store
  - conformance A-D suite automation (12 cases) and CI artifact generation

### CI
- CI now runs governance checks, unit tests, conformance suite, and uploads artifacts:
  - `summary.json`
  - `scenario-results.jsonl`
  - `quarantine-records.jsonl`
  - `node-state-hashes.json`

### Verification
- Unit and integration-like tests: passed (`12` tests)
- Conformance run: passed with artifact output under `artifacts/conformance`

### Known Constraints
- QUIC transport is still not fully wired to real network interoperability scenarios.
- Persistence backend remains prototype-level for production crash-safety requirements.
- CI conformance thresholds are implemented but may need stricter production tuning.
