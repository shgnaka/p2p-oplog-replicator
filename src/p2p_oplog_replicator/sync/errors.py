from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationErrorDetail:
    code: str
    message: str


class ValidationError(Exception):
    def __init__(self, detail: ValidationErrorDetail) -> None:
        super().__init__(f"{detail.code}: {detail.message}")
        self.detail = detail
