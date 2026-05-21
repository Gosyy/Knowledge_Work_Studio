from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

QUALITY_DOCS = (
    "docs/quality/QUALITY_GATES.md",
    "docs/quality/RENDER_AND_VISUAL_QA.md",
    "docs/quality/XLSX_VALIDATION.md",
)

QUALITY_BRIDGES = (
    "scripts/kw_kq1_deck_quality_check.py",
    "scripts/kw_kq1b_exec_memo_pptx_check.py",
    "scripts/kw_kq1c_independent_render_check.py",
    "scripts/kw_product_docs_check.py",
)


def test_quality_docs_exist_for_product_gate_categories() -> None:
    missing = [path for path in QUALITY_DOCS if not (REPO_ROOT / path).exists()]
    assert missing == []


def test_slides_quality_aliases_bridge_to_accepted_render_pipeline() -> None:
    missing = [path for path in QUALITY_BRIDGES if not (REPO_ROOT / path).exists()]
    assert missing == []


def test_quality_gate_language_does_not_claim_kimi_level() -> None:
    quality_text = (REPO_ROOT / "docs/quality/QUALITY_GATES.md").read_text(encoding="utf-8")
    lower = quality_text.lower()
    forbidden_positive_claims = (
        "kimi-level achieved",
        "kimi-level: ready",
        "kimi-level quality achieved",
        "kimi-level parity",
    )
    assert all(claim not in lower for claim in forbidden_positive_claims)
    if "kimi-level" in lower:
        assert "does not prove" in lower or "not claim" in lower or "not claimed" in lower
    assert "artifact" in lower
