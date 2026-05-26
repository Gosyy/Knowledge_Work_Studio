#!/usr/bin/env python3
"""Validate KR-7E offline evidence index and unsupported-claim guardrails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "backend/app/services/slides_service/offline_evidence_index.py",
    "backend/tests/services/test_kr7e_offline_evidence_index.py",
]

REQUIRED_PHRASES = {
    "backend/app/services/slides_service/offline_evidence_index.py": [
        'OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION = "offline_evidence_index.v1"',
        "class OfflineEvidenceIndexBuilder",
        "def build_index",
        "def search",
        "def assess_claim",
        "def search_sections",
        "class EvidenceSectionScore",
        "class UnsupportedClaimReport",
        "OFFLINE_UNSUPPORTED_CLAIM_REPORT_SCHEMA_VERSION",
        "coverage_ratio",
        "missing_terms",
        "section_scoring_hardened",
        "unsupported_claim_report_schema",
        "no_hidden_embedding_dependency",
        "no_web_research",
        "postgres_fts_runtime",
        "planned_not_claimed_in_kr7e1",
    ],
    "backend/tests/services/test_kr7e_offline_evidence_index.py": [
        "test_kr7e_evidence_index_builds_lexical_records_from_ingestion_report",
        "test_kr7e_evidence_index_search_returns_source_backed_evidence",
        "test_kr7e_evidence_index_assesses_supported_and_unsupported_claims",
        "test_kr7e_prompt_only_index_does_not_claim_research_backing",
        "test_kr7e_unsupported_sources_are_reported_honestly",
        "test_kr7e2_search_results_include_section_scores_and_coverage",
        "test_kr7e2_unsupported_claim_report_lists_missing_terms_and_candidate_sections",
        "test_kr7e2_prompt_only_unsupported_report_is_structured",
    ],
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md": [
        "KR-7E.1 Offline evidence index foundation",
        "KR-7E.2 evidence-to-source-section scoring and unsupported-claim reporting hardening",
        "offline_evidence_index.v1",
        "no hidden embedding dependency",
    ],
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md": [
        "KR-7E.1 introduces an offline evidence index foundation",
        "lexical_token_index",
        "BM25-like IDF scoring",
        "KR-7E.2 hardens evidence-to-source-section scoring",
    ],
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md": [
        "KR-7E.1 Offline evidence index foundation",
        "prompt-only decks must not be treated as research-backed",
        "KR-7E.2 evidence-to-source-section scoring and unsupported-claim reporting hardening",
    ],
    "docs/QUALITY_MATRIX.md": [
        "KR-7E.1 adds offline evidence index foundation",
        "KR-7E.2 hardens section scoring",
    ],
    "docs/PROJECT_PROHIBITIONS.md": [
        "claim research-backed evidence for prompt-only decks",
        "claim embeddings or PostgreSQL FTS runtime from KR-7E.1",
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
        "schema_version": "kw_offline_evidence_index_check.v1",
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
        print(f"kw_offline_evidence_index_check.py: {result['status']}")
        if result["status"] != "ready":
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and result["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
