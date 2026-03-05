# MVP Protocol Draft

## Wire

- Transport: JSON over QUIC
- Envelope types: `HELLO`, `ACK`, `REQUEST`, `PUSH`

## Message Types

### HELLO

- Fields: `type`, `node_id`, `protocol_version`, `capabilities`, `timestamp`

### ACK

- Fields: `type`, `ack_for`, `status`, `reason?`, `timestamp`

### REQUEST

- Fields: `type`, `request_id`, `cursor`, `limit`, `timestamp`

### PUSH

- Fields: `type`, `request_id?`, `events[]`, `timestamp`

## Event Envelope

- Required keys:
  - `event_id`
  - `event_version`
  - `merge_strategy`
  - `causal` (tagged-union; Lamport as MVP variant)
  - `command_schema`
  - `command`
  - `signature` (Ed25519)
  - `author`
  - `created_at`

## Sync Invariants

- Idempotent apply by `event_id`
- LWW+tombstone in MVP
- Deterministic reducer only
- Signature verification required before apply
