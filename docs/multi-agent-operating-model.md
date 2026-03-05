# Multi-Agent Operating Model

This repository follows a fixed six-agent model.

## Agents and Ownership

1. PM/Orchestrator Agent
- Owns roadmap, issue slicing, dependency graph, and DoD checks.

2. Protocol Architect Agent
- Owns wire-level contracts and schema compatibility.
- Required reviewer for protocol surface changes.

3. Coding Agent A (Connectivity)
- Owns peer discovery, connection attempts, retry and transport resilience.

4. Coding Agent B (Sync Core)
- Owns signed event replication, idempotency, LWW+tombstone reducer behavior.

5. Testing/Validation Agent
- Owns conformance tests A-D and scenario validation.

6. Reviewer/Security Agent
- Owns cryptography, threat checks, and merge gate decisions.

## Execution Order

- Phase 1: Connectivity foundation
- Phase 2: Sync core
- Phase 3: Validation and CRDT migration readiness

## Non-Negotiable Rules

- Deterministic reducers only.
- Protocol-breaking changes require explicit version bumps.
- Protocol/schema edits are serialized by ownership (single active branch at a time).
