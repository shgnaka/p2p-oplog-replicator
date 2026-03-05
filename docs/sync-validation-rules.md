# Sync Validation Rules (E2)

## Signature Verification

- Algorithm: Ed25519
- Trust source: fixed member public key list
- Verification target: canonical JSON encoding of event envelope excluding transport metadata

Invalid signature handling:
- Do not apply to state
- Write reject audit entry
- Keep reject reason with event_id and peer_id

## Idempotency Contract

- Primary key: `event_id`
- If `event_id` already applied, treat as idempotent success and skip reducer execution.
- If `event_id` exists with different payload hash, classify as integrity conflict and quarantine.

## Quarantine Triggers

- Unknown `command_schema`
- Unsupported `event_version`
- Signature verification failure
- Integrity conflict (`event_id` collision with mismatched hash)

## Error Categories

- `ERR_SIG_INVALID`
- `ERR_SCHEMA_UNKNOWN`
- `ERR_EVENT_VERSION_UNSUPPORTED`
- `ERR_EVENT_ID_CONFLICT`
