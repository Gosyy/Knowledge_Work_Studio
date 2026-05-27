#!/usr/bin/env python3
"""Validate KR-7G visual grammar library foundation guardrails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "backend/app/services/slides_service/visual_grammar.py",
    "backend/tests/services/test_kr7g_visual_grammar.py",
    "backend/app/services/slides_service/presentation_ir_planner.py",
    "backend/app/api/routes/presentation_api_v1.py",
    "backend/app/api/schemas/presentations.py",
]

REQUIRED_PHRASES = {
    "backend/app/services/slides_service/visual_grammar.py": [
        'VISUAL_GRAMMAR_SCHEMA_VERSION = "presentation_visual_grammar.v1"',
        "class VisualGrammarBlockSpec",
        "class VisualGrammarValidationResult",
        "class PresentationVisualGrammarLibrary",
        "def validate_block",
        "def validate_presentation_ir_blocks",
        "visual_grammar_catalog_payload",
        "executive_summary_cards",
        "kpi_cards",
        "process_flow",
        "roadmap",
        "timeline",
        "two_by_two_matrix",
        "swot",
        "comparison_table",
        "decision_matrix",
        "risk_matrix",
        "architecture_diagram",
        "funnel",
        "data_table",
        "native_chart",
        "native_chart_requires_real_numeric_data",
        "no_fake_charts_or_values",
        "does not render PPTX",
        "does not render PPTX, call LLMs, create charts, generate images, or fabricate",
    ],
    "backend/app/services/slides_service/presentation_ir_planner.py": [
        "PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION",
        "PresentationVisualGrammarLibrary",
        "_visual_grammar_block",
        "visual_grammar_bound_blocks",
        "visual_grammar_binding_status",
        "unsupported_outline_without_source_evidence",
    ],
    "backend/app/api/routes/presentation_api_v1.py": [
        "def get_presentation_visual_grammar_catalog_v1",
        "def get_presentation_visual_grammar_v1",
        "_visual_grammar_bindings_from_ir",
        "renderer_runtime_implemented=False",
        "PresentationVisualGrammarLibrary",
    ],
    "backend/app/api/schemas/presentations.py": [
        "class PresentationVisualGrammarCatalogResponseSchema",
        "class PresentationVisualGrammarReadResponseSchema",
        "class PresentationVisualGrammarBindingReadSchema",
        "class PresentationVisualGrammarValidationResultSchema",
        "presentation_visual_grammar_catalog_read.v1",
    ],
    "backend/tests/services/test_kr7g_visual_grammar.py": [
        "test_kr7g1_visual_grammar_catalog_contains_required_editable_blocks",
        "test_kr7g1_visual_grammar_validates_source_backed_cards",
        "test_kr7g1_visual_grammar_blocks_chart_without_real_numeric_source_data",
        "test_kr7g1_visual_grammar_accepts_native_chart_with_source_data_ref_and_numeric_series",
        "test_kr7g1_visual_grammar_validates_diagram_nodes_or_items",
    ],
    "backend/tests/api/test_kr7c_presentation_api_contract.py": [
        "test_kr7g3_visual_grammar_catalog_api_exposes_read_only_contract",
        "test_kr7g3_visual_grammar_read_api_validates_presentation_ir_bindings",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7G.1 visual grammar library foundation",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
        "KR-7G.3 visual grammar API/catalog/read contract hardening",
        "KR-7G.3 visual grammar API/catalog/read contract hardening",
        "presentation_visual_grammar.v1",
        "every block has semantic purpose and validator",
        "native chart blocks require real numeric data and source data refs",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
        "KR-7G.3 visual grammar API/catalog/read contract hardening",
        "KR-7G.3 visual grammar API/catalog/read contract hardening",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "Phase KR-7G — visual grammar library",
        "KR-7G.1 introduces presentation_visual_grammar.v1",
        "KR-7G.2 binds presentation_visual_grammar.v1 blocks",
        "KR-7G.3 exposes read-only visual grammar catalog and binding validation APIs",
        "fake chart values are forbidden",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7G.1 visual grammar library foundation",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
        "KR-7G.3 visual grammar API/catalog/read contract hardening",
        "KR-7G.3 visual grammar API/catalog/read contract hardening",
        "presentation_visual_grammar.v1",
        "native_chart_requires_real_numeric_data",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7G.1 adds visual grammar library foundation",
        "KR-7G.2 binds visual grammar blocks",
        "KR-7G.3 exposes visual grammar read contracts without renderer claims",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim KR-7G.1 renders PPTX or native visuals",
        "accept native_chart visual grammar blocks without real numeric source data",
        "claim visual grammar blocks are source-backed when planner output has no evidence bindings",
        "claim visual grammar catalog/read APIs render PPTX or generate visual output",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check(repo_root: Path) -> dict[str, Any]:
    missing_files = [path for path in REQUIRED_FILES if not (repo_root / path).is_file()]
    missing_phrases: dict[str, list[str]] = {}
    for relative_path, phrases in REQUIRED_PHRASES.items():
        path = repo_root / relative_path
        if not path.is_file():
            missing_phrases[relative_path] = phrases
            continue
        text = _read(path)
        absent = [phrase for phrase in phrases if phrase not in text]
        if absent:
            missing_phrases[relative_path] = absent
    status = "ready" if not missing_files and not missing_phrases else "blocked"
    return {
        "status": status,
        "schema_version": "kw_visual_grammar_check.v1",
        "missing_files": missing_files,
        "missing_phrases": missing_phrases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"kw_visual_grammar_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
