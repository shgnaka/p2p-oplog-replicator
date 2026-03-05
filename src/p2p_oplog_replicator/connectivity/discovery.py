from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PeerCandidate:
    """Candidate peer endpoint discovered via DHT/PEX-like providers."""

    peer_id: str
    address: str
    source: str


class DiscoveryProvider(ABC):
    """Abstract discovery provider (e.g. DHT, PEX)."""

    @abstractmethod
    def discover(self) -> Iterable[PeerCandidate]:
        """Return newly discovered peer candidates."""


class DiscoveryCoordinator:
    """Collects candidates from registered discovery providers."""

    def __init__(self) -> None:
        self._providers: list[DiscoveryProvider] = []

    def register_provider(self, provider: DiscoveryProvider) -> None:
        self._providers.append(provider)

    def poll(self) -> list[PeerCandidate]:
        discovered: list[PeerCandidate] = []
        for provider in self._providers:
            discovered.extend(provider.discover())
        return discovered
