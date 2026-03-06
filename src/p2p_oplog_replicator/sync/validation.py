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

_ALLOWED_MERGE_STRATEGIES = {"lww_tombstone"}
_ALLOWED_COMMAND_OPS = {"set", "delete"}


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

        if event.get("merge_strategy") not in _ALLOWED_MERGE_STRATEGIES:
            raise ValidationError(
                ValidationErrorDetail(
                    "ERR_SCHEMA_UNKNOWN",
                    f"unsupported merge_strategy: {event.get('merge_strategy')}",
                )
            )

        self._validate_scalar_fields(event)
        self._validate_causal(event.get("causal"))
        self._validate_command(event.get("command"))

        canonical = _canonical_signing_payload(event)
        if not self._verifier.verify(
            author=event["author"],
            signature_b64=event["signature"],
            payload=canonical,
        ):
            raise ValidationError(ValidationErrorDetail("ERR_SIG_INVALID", "signature verification failed"))

        return ValidatedEvent(event=event, canonical_payload=canonical)

    @staticmethod
    def _validate_scalar_fields(event: dict) -> None:
        if not isinstance(event.get("event_id"), str) or not event["event_id"]:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "event_id must be non-empty string"))
        if not isinstance(event.get("author"), str) or not event["author"]:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "author must be non-empty string"))
        if not isinstance(event.get("created_at"), str) or not event["created_at"]:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "created_at must be non-empty string"))

    @staticmethod
    def _validate_causal(causal: object) -> None:
        if not isinstance(causal, dict) or causal.get("type") != "lamport_v1":
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "causal must be lamport_v1 object"))
        lamport = causal.get("lamport")
        if not isinstance(lamport, int) or lamport < 0:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "causal.lamport must be non-negative int"))
        node_id = causal.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "causal.node_id must be non-empty string"))

    @staticmethod
    def _validate_command(command: object) -> None:
        if not isinstance(command, dict):
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "command must be object"))
        op = command.get("op")
        if op not in _ALLOWED_COMMAND_OPS:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "command.op must be set/delete"))
        key = command.get("key")
        if not isinstance(key, str) or not key:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "command.key must be non-empty string"))
        if op == "set" and "value" not in command:
            raise ValidationError(ValidationErrorDetail("ERR_SCHEMA_UNKNOWN", "set command must include value"))


def _canonical_signing_payload(event: dict) -> bytes:
    for_signing = {k: v for k, v in event.items() if k != "signature"}
    return json.dumps(for_signing, sort_keys=True, separators=(",", ":")).encode("utf-8")
