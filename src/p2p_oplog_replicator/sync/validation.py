from __future__ import annotations

import json
from dataclasses import dataclass

from p2p_oplog_replicator.crypto.signature import Ed25519Verifier
from p2p_oplog_replicator.sync.errors import ValidationError, ValidationErrorDetail

REQUIRED_KEYS = {
    "event_id",
    "event_version",
    "merge_strategy",
    "causal",
    "command_schema",
    "command",
    "signature",
    "author",
    "created_at",
}


@dataclass(frozen=True)
class ValidatedEvent:
    event: dict
    canonical_payload: bytes


class EventEnvelopeValidator:
    """Schema-key validation + Ed25519 verification for inbound events."""

    def __init__(self, verifier: Ed25519Verifier) -> None:
        self._verifier = verifier

    def validate(self, event: dict) -> ValidatedEvent:
        if not isinstance(event, dict):
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "event must be an object"))

        missing = sorted(REQUIRED_KEYS - set(event.keys()))
        if missing:
            raise ValidationError(
                ValidationErrorDetail(
                    "ERR_SCHEMA_UNKNOWN",
                    f"missing required keys: {missing}",
                )
            )

        if event.get("event_version") != "lww_v1":
            raise ValidationError(
                ValidationErrorDetail(
                    "ERR_EVENT_VERSION_UNSUPPORTED",
                    f"unsupported event_version: {event.get('event_version')}",
                )
            )

        if not isinstance(event.get("causal"), dict) or event["causal"].get("type") != "lamport_v1":
            raise ValidationError(
                ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "causal must be lamport_v1 object")
            )

        canonical = _canonical_signing_payload(event)
        if not self._verifier.verify(
            author=event["author"],
            signature_b64=event["signature"],
            payload=canonical,
        ):
            raise ValidationError(ValidationErrorDetail("ERR_SIG_INVALID", "signature verification failed"))

        return ValidatedEvent(event=event, canonical_payload=canonical)


def _canonical_signing_payload(event: dict) -> bytes:
    for_signing = {k: v for k, v in event.items() if k != "signature"}
    return json.dumps(for_signing, sort_keys=True, separators=(",", ":")).encode("utf-8")
