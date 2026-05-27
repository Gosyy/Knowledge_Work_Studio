#!/usr/bin/env python3
"""Validate KR-7F PresentationIR planner and outline guardrails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "backend/app/services/slides_service/presentation_ir_planner.py",
    "backend/tests/services/test_kr7f_presentation_ir_planner.py",
]

REQUIRED_PHRASES = {
    "backend/app/services/slides_service/presentation_ir_planner.py": [
        'PRESENTATION_IR_PLANNER_SCHEMA_VERSION = "presentation_ir_planner.v1"',
        'PRESENTATION_IR_OUTLINE_SCHEMA_VERSION = "presentation_ir_outline.v1"',
        'PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION = "presentation_ir_planner_snapshot.v1"',
        'PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION = "presentation_ir_visual_grammar_binding.v1"',
        "class PresentationIRPlannerFoundation",
        "class PresentationIRPlannerRequest",
        "class PresentationIRPlannerResult",
        "class PresentationIRSlideOutline",
        "presentation_ir_planner_snapshot_metadata",
        "presentation_ir_planner_snapshot_metadata_from_ir",
        "require_persistable_presentation_ir_planner_result",
        "def plan_from_evidence",
        "require_presentation_ir_payload",
        "evidence_required_but_index_empty",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
        "prompt_only_degraded_planner_output_without_source_evidence",
        "evidence_aware_outline_planning",
        "outline_coverage_ratio",
        "slide_outline_missing_expected_terms",
        "no_fake_charts",
        "no_generated_images",
        "requires_chart",
        "requires_image",
        "does not call LLMs",
        "KR-7F.2 hardens",
        "Blocked PresentationIR planner results cannot be persisted",
        "PresentationVisualGrammarLibrary",
        "VISUAL_GRAMMAR_SCHEMA_VERSION",
        "_visual_grammar_block",
        "_visual_grammar_summary",
        "visual_grammar_bound_blocks",
        "visual_grammar_binding_status",
    ],
    "backend/tests/services/test_kr7f_presentation_ir_planner.py": [
        "test_kr7f1_planner_builds_valid_presentation_ir_from_offline_evidence",
        "test_kr7f1_planner_blocks_when_source_evidence_required_but_missing",
        "test_kr7f1_prompt_only_planner_output_is_degraded_and_explicit",
        "test_kr7f1_planner_does_not_require_images_or_fake_charts",
        "test_kr7f2_planner_emits_evidence_aware_slide_outlines",
        "test_kr7f2_planner_degrades_when_outline_coverage_is_below_threshold",
        "test_kr7f2_prompt_only_outline_marks_every_slide_unsupported",
        "test_kr7f3_planner_result_embeds_persistable_snapshot_metadata",
        "test_kr7f3_blocked_planner_result_is_not_persistable_as_ir_snapshot",
        "test_kr7g2_planner_binds_visual_grammar_blocks_into_presentation_ir",
        "test_kr7g2_planner_uses_data_table_instead_of_fake_native_chart_for_data_role",
        "test_kr7g2_prompt_only_output_does_not_bind_source_backed_visual_grammar_blocks",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7F.1 PresentationIR planner foundation",
        "KR-7F.2 evidence-aware slide outline planning hardening",
        "KR-7F.3 planner persistence and PresentationIR snapshot API contract hardening",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
        "presentation_ir_planner.v1",
        "presentation_ir_outline.v1",
        "do not claim final GigaChat planning runtime from KR-7F.1",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7F.1 introduces a deterministic PresentationIR planner foundation",
        "KR-7F.2 hardens evidence-aware slide outline planning",
        "KR-7F.3 hardens planner persistence and PresentationIR snapshot API contract",
        "KR-7G.2 binds visual grammar blocks",
        "KR-7G.2 binds presentation_visual_grammar.v1 blocks",
        "presentation_ir_planner.v1",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7F.1 PresentationIR planner foundation",
        "KR-7F.2 evidence-aware slide outline planning hardening",
        "KR-7F.3 planner persistence and PresentationIR snapshot API contract hardening",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
        "evidence_required_but_index_empty",
        "KR-7G.2 bind visual grammar blocks into PresentationIR planner output",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7F.1 adds PresentationIR planner foundation",
        "KR-7F.2 hardens evidence-aware slide outline planning",
        "KR-7F.3 hardens planner persistence and PresentationIR snapshot API contract",
        "KR-7G.2 binds visual grammar blocks",
        "KR-7G.2 binds presentation_visual_grammar.v1 blocks",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim final GigaChat PresentationIR planning runtime from KR-7F.1",
        "claim prompt-only degraded planner drafts are source-backed",
        "claim evidence-aware slide outline planning is final GigaChat planning runtime",
        "claim blocked planner results are persistable PresentationIR snapshots",
        "claim visual grammar blocks are source-backed when planner output has no evidence bindings",
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
        "schema_version": "kw_presentation_ir_planner_check.v1",
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
        print(f"kw_presentation_ir_planner_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
