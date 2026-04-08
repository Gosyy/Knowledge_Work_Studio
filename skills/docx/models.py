from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocxEditPlan:
    operation: str
    target: str
    replacement: str
