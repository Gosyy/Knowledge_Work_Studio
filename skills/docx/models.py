from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocxEditPlan:
    operation: str
    target: str
    replacement: str


@dataclass(frozen=True)
class DocxRewritePlan:
    replacements: tuple[tuple[str, str], ...]
    normalize_headings: bool = True
