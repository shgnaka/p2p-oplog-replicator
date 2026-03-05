from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from p2p_oplog_replicator.persistence.file_backend import DurableAtomicJsonFileStore
from p2p_oplog_replicator.sync.errors import ValidationError, ValidationErrorDetail


@dataclass(frozen=True)
class IndexRecord:
    event_id: str
    payload_hash: str


class EventIdempotencyIndex:
    """Tracks event_id -> payload hash for duplicate/no-op and conflict detection."""

    def __init__(self) -> None:
        self._index: dict[str, IndexRecord] = {}

    def register(self, event: dict) -> bool:
        event_id = event["event_id"]
        payload_hash = _payload_hash(event)
        current = self._index.get(event_id)
        if current is None:
            self._index[event_id] = IndexRecord(event_id=event_id, payload_hash=payload_hash)
            return True
        if current.payload_hash == payload_hash:
            return False
        raise ValidationError(
            ValidationErrorDetail(
                "ERR_EVENT_ID_CONFLICT",
                f"event_id={event_id} already indexed with different payload hash",
            )
        )

    def has(self, event_id: str) -> bool:
        return event_id in self._index


class PersistentEventIdempotencyIndex(EventIdempotencyIndex):
    """Event idempotency index persisted atomically as JSON snapshots."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._store = DurableAtomicJsonFileStore(path, default_payload={"records": {}})
        self._load()

    def register(self, event: dict) -> bool:
        changed = super().register(event)
        if changed:
            self._store.store_json(
                {
                    "records": {
                        event_id: asdict(record)
                        for event_id, record in sorted(self._index.items())
                    }
                }
            )
        return changed

    def _load(self) -> None:
        raw = self._store.load_json().get("records", {})
        for event_id, record in raw.items():
            self._index[event_id] = IndexRecord(
                event_id=str(event_id),
                payload_hash=str(record["payload_hash"]),
            )


def _payload_hash(event: dict) -> str:
    canonical = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
