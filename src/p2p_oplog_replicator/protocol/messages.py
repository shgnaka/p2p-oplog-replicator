from __future__ import annotations

import json
from enum import Enum


class MalformedMessageError(ValueError):
    pass


class MessageType(str, Enum):
    HELLO = "HELLO"
    ACK = "ACK"
    REQUEST = "REQUEST"
    PUSH = "PUSH"


_REQUIRED_FIELDS: dict[MessageType, set[str]] = {
    MessageType.HELLO: {"type", "node_id", "protocol_version", "capabilities", "timestamp"},
    MessageType.ACK: {"type", "ack_for", "status", "timestamp"},
    MessageType.REQUEST: {"type", "request_id", "cursor", "limit", "timestamp"},
    MessageType.PUSH: {"type", "events", "timestamp"},
}


_ACK_STATUS = {"ok", "error"}


def encode_message(message: dict) -> bytes:
    validated = validate_message(message)
    return json.dumps(validated, separators=(",", ":"), sort_keys=True).encode("utf-8")


def decode_message(payload: bytes) -> dict:
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MalformedMessageError("payload is not valid UTF-8 JSON") from exc
    return validate_message(raw)


def validate_message(message: dict) -> dict:
    if not isinstance(message, dict):
        raise MalformedMessageError("message must be a JSON object")
    message_type = message.get("type")
    try:
        mtype = MessageType(message_type)
    except ValueError as exc:
        raise MalformedMessageError(f"unsupported message type: {message_type}") from exc

    missing = _REQUIRED_FIELDS[mtype] - set(message.keys())
    if missing:
        raise MalformedMessageError(f"missing required fields for {mtype.value}: {sorted(missing)}")

    timestamp = message.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        raise MalformedMessageError(f"{mtype.value}.timestamp must be a non-empty string")

    if mtype == MessageType.PUSH:
        if not isinstance(message.get("events"), list):
            raise MalformedMessageError("PUSH.events must be a list")
    if mtype == MessageType.HELLO:
        if not isinstance(message.get("capabilities"), list):
            raise MalformedMessageError("HELLO.capabilities must be a list")
    if mtype == MessageType.ACK:
        status = message.get("status")
        if status not in _ACK_STATUS:
            raise MalformedMessageError("ACK.status must be one of: ok,error")
    if mtype == MessageType.REQUEST:
        cursor = message.get("cursor")
        limit = message.get("limit")
        if not isinstance(cursor, str) or not cursor:
            raise MalformedMessageError("REQUEST.cursor must be a non-empty string")
        if not isinstance(limit, int) or limit <= 0:
            raise MalformedMessageError("REQUEST.limit must be a positive integer")

    return message
