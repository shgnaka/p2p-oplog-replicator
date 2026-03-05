# Connectivity Architecture (E1)

## Purpose

Define lower-layer connectivity responsibilities separated from sync semantics.

## Module Boundaries

- `discovery`: collects peer candidates from DHT/PEX abstractions.
- `dialer`: attempts QUIC channel establishment against candidates.
- `session`: exposes connected peer sessions to upper sync layer.
- `recovery`: retries failed connects and drives missing-data requests.

## Contracts for Upper Layer

- Upper layer receives events:
  - `peer_connected(peer_id, session_id)`
  - `peer_disconnected(peer_id, reason)`
  - `message_received(session_id, payload_bytes)`
- Upper layer can request:
  - `send(session_id, payload_bytes)`
  - `broadcast(payload_bytes, filter)`
  - `request_recovery(peer_id, from_cursor)`

## Candidate Lifecycle

`discovered -> queued -> dialing -> connected|failed -> retriable|dead`

## Retry Policy Baseline

- Exponential backoff with jitter.
- Cap retries per peer in rolling window.
- Reset counters after successful stable session.

## Non-Goals

- Relay/TURN support.
- Application-level merge/reducer logic.
