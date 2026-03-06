from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterDecision:
    event_id: str
    adapter_version: str
    decision: str
    reason_code: str
    explain: str
    crdt_ops: list[dict]


class LwwToCrdtAdapter:
    """Deterministic adapter from lww_v1 events to crdt_x_v1 operations."""

    def __init__(self, adapter_version: str = "adapter_v1") -> None:
        self._version = adapter_version

    def convert(self, event: dict) -> AdapterDecision:
        event_id = event.get("event_id", "")
        schema = event.get("command_schema", "")
        if event.get("event_version") != "lww_v1":
            return AdapterDecision(
                event_id=event_id,
                adapter_version=self._version,
                decision="QUARANTINE",
                reason_code="Q_VERSION_UNSUPPORTED",
                explain="event_version is not lww_v1",
                crdt_ops=[],
            )
        if schema != "todo.v1":
            return AdapterDecision(
                event_id=event_id,
                adapter_version=self._version,
                decision="QUARANTINE",
                reason_code="Q_UNSUPPORTED_SCHEMA",
                explain="command_schema is not supported by this adapter",
                crdt_ops=[],
            )

        causal = event.get("causal", {})
        lamport = causal.get("lamport")
        node_id = causal.get("node_id")
        if not isinstance(lamport, int) or lamport < 0:
            return AdapterDecision(
                event_id=event_id,
                adapter_version=self._version,
                decision="QUARANTINE",
                reason_code="Q_INVALID_CAUSAL_CLOCK",
                explain="causal.lamport must be non-negative int",
                crdt_ops=[],
            )
        if not isinstance(node_id, str) or not node_id:
            return AdapterDecision(
                event_id=event_id,
                adapter_version=self._version,
                decision="QUARANTINE",
                reason_code="Q_INVALID_CAUSAL_NODE",
                explain="causal.node_id must be non-empty string",
                crdt_ops=[],
            )

        command = event.get("command", {})
        op = command.get("op")
        key = command.get("key")
        if not isinstance(key, str) or not key:
            return AdapterDecision(
                event_id=event_id,
                adapter_version=self._version,
                decision="QUARANTINE",
                reason_code="Q_MISSING_COMMAND_KEY",
                explain="command.key must be non-empty string",
                crdt_ops=[],
            )
        if op not in {"set", "delete"}:
            return AdapterDecision(
                event_id=event_id,
                adapter_version=self._version,
                decision="QUARANTINE",
                reason_code="Q_UNSUPPORTED_COMMAND_OP",
                explain="command.op is unsupported",
                crdt_ops=[],
            )

        crdt_op = {
            "type": "crdt_x_v1",
            "entity": key,
            "action": op,
            "value": command.get("value"),
            "clock": {"lamport": lamport, "node_id": node_id},
        }
        return AdapterDecision(
            event_id=event_id,
            adapter_version=self._version,
            decision="APPLY",
            reason_code="",
            explain="converted",
            crdt_ops=[crdt_op],
        )
