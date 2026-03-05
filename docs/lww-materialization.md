# LWW + Tombstone Materialization (E2)

## Deterministic Resolution Rule

For each logical entity key:
- Compare `(lamport, author)` tuple.
- Larger lamport wins.
- If lamport ties, lexical order of `author` is tie-breaker.

This yields deterministic winner selection across nodes.

## Tombstone Handling

- Delete is represented as tombstone event.
- A tombstoned key cannot reappear unless a strictly newer winning event exists by tuple rule.
- Replays must not resurrect stale pre-tombstone values.

## Apply Steps

1. Validate event envelope and signature.
2. Resolve winner against current entity head using tuple rule.
3. Update materialized view and tombstone index atomically.
4. Emit deterministic state delta.

## Invariants

- Same ordered event set => same final materialized state.
- Duplicate events do not change state after first apply.
- Tombstone prevents stale value reappearance.
