from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PeerEndpoint:
    peer_id: str
    host: str
    port: int


@dataclass(frozen=True)
class WireEnvelope:
    msg_type: str
    payload: dict


class IncomingMessageSink(Protocol):
    def on_message(self, session_id: str, envelope: WireEnvelope) -> None:
        ...


class QuicTransport(Protocol):
    async def start(self, host: str, port: int) -> tuple[str, int]:
        ...

    async def stop(self) -> None:
        ...

    async def connect(self, endpoint: PeerEndpoint) -> str:
        ...

    async def send(self, session_id: str, envelope: WireEnvelope) -> None:
        ...

    async def disconnect(self, session_id: str, reason: str) -> None:
        ...
