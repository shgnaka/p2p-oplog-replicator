from __future__ import annotations

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class Ed25519Verifier:
    """Ed25519 verifier against a fixed member public-key registry."""

    def __init__(self, member_public_keys: dict[str, str]) -> None:
        self._keys = {
            member: Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))
            for member, pub_b64 in member_public_keys.items()
        }

    def verify(self, author: str, signature_b64: str, payload: bytes) -> bool:
        key = self._keys.get(author)
        if key is None:
            return False
        try:
            key.verify(base64.b64decode(signature_b64), payload)
            return True
        except (InvalidSignature, ValueError):
            return False
