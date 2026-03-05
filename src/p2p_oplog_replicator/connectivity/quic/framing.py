from __future__ import annotations

import json

from p2p_oplog_replicator.connectivity.quic.contracts import WireEnvelope


class FrameError(ValueError):
    pass


def encode_frame(envelope: WireEnvelope) -> bytes:
    raw = {
        "type": envelope.msg_type,
        "payload": envelope.payload,
    }
    return (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def decode_frame(frame: bytes) -> WireEnvelope:
    try:
        obj = json.loads(frame.decode("utf-8").strip())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrameError("invalid frame encoding") from exc
    if not isinstance(obj, dict) or "type" not in obj or "payload" not in obj:
        raise FrameError("invalid frame structure")
    if not isinstance(obj["payload"], dict):
        raise FrameError("payload must be object")
    return WireEnvelope(msg_type=str(obj["type"]), payload=obj["payload"])
