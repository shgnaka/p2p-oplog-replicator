from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class SessionEventType(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass(frozen=True)
class SessionEvent:
    event_type: SessionEventType
    peer_id: str
    session_id: str
    reason: str = ""


class SessionEventSink(Protocol):
    def on_event(self, event: SessionEvent) -> None:
        ...


@dataclass(frozen=True)
class Session:
    peer_id: str
    session_id: str


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._sinks: list[SessionEventSink] = []

    def register_sink(self, sink: SessionEventSink) -> None:
        self._sinks.append(sink)

    def register_connected(self, session: Session) -> None:
        self._sessions[session.peer_id] = session
        self._emit(
            SessionEvent(
                event_type=SessionEventType.CONNECTED,
                peer_id=session.peer_id,
                session_id=session.session_id,
            )
        )

    def disconnect(self, peer_id: str, reason: str) -> None:
        session = self._sessions.pop(peer_id)
        self._emit(
            SessionEvent(
                event_type=SessionEventType.DISCONNECTED,
                peer_id=peer_id,
                session_id=session.session_id,
                reason=reason,
            )
        )

    def has_session(self, peer_id: str) -> bool:
        return peer_id in self._sessions

    def _emit(self, event: SessionEvent) -> None:
        for sink in self._sinks:
            sink.on_event(event)
