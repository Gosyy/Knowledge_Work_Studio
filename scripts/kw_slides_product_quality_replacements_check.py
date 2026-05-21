#!/usr/bin/env python3
"""KR-2E Slides product quality replacement coverage check.

KR-2E is an additive bridge from KQ-1A/B/C stage-named tests to product-named
Slides quality/workflow tests. It does not remove KQ tests or move docs/codex.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRODUCT_SLIDES_TESTS: tuple[str, ...] = (
    "backend/tests/quality/test_artifact_bundle_quality_product_contract.py",
    "backend/tests/workflows/test_slides_exec_memo_generation_product_contract.py",
    "backend/tests/quality/test_pptx_render_qa_product_contract.py",
    "backend/tests/smoke/test_slides_product_quality_replacements.py",
)

LEGACY_KQ_SAFETY_NETS: tuple[str, ...] = (
    "backend/tests/smoke/test_kq1_deck_quality.py",
    "backend/tests/smoke/test_kq1b_exec_memo_deck_generation.py",
    "backend/tests/smoke/test_kq1c_independent_render_qa.py",
    "scripts/kw_kq1_deck_quality_check.py",
    "scripts/kw_kq1b_exec_memo_pptx_check.py",
    "scripts/kw_kq1c_independent_render_check.py",
)

PRODUCT_SLIDES_DOCS: tuple[str, ...] = (
    "docs/workflows/SLIDES_WORKFLOW.md",
    "docs/quality/RENDER_AND_VISUAL_QA.md",
    "docs/quality/QUALITY_GATES.md",
)

SUPPORT_FILES: tuple[str, ...] = (
    "scripts/kw_slides_product_quality_replacements_check.py",
    "docs/refactor/SLIDES_PRODUCT_QUALITY_REPLACEMENT_TESTS.md",
)

FORBIDDEN_POSITIVE_CLAIMS: tuple[str, ...] = (
    "kimi-level achieved",
    "kimi-level: ready",
    "kimi-level quality achieved",
    "kimi-level parity",
    "selected workflow parity achieved",
)


@dataclass(frozen=True)
class FileStatus:
    path: str
    exists: bool
    status: str
    reason: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def file_status(repo_root: Path, path: str, *, role: str) -> FileStatus:
    exists = (repo_root / path).exists()
    return FileStatus(path=path, exists=exists, status="ready" if exists else "missing", reason=f"{role} {'exists' if exists else 'is missing'}")


def read_text_if_exists(repo_root: Path, path: str) -> str:
    full_path = repo_root / path
    if not full_path.exists():
        return ""
    return full_path.read_text(encoding="utf-8")


def scan_positive_claims(repo_root: Path) -> list[str]:
    issues: list[str] = []
    for rel_path in PRODUCT_SLIDES_DOCS + PRODUCT_SLIDES_TESTS:
        text = read_text_if_exists(repo_root, rel_path).lower()
        for claim in FORBIDDEN_POSITIVE_CLAIMS:
            if claim in text:
                issues.append(f"{rel_path}: contains unsupported positive claim {claim!r}")
    return issues


def check_docs_codex_not_moved(repo_root: Path) -> list[str]:
    codex_dir = repo_root / "docs" / "codex"
    if not codex_dir.exists():
        return ["docs/codex is missing; physical archive remains blocked until stage checkers/tests are rewritten"]
    if not any(codex_dir.glob("*.md")):
        return ["docs/codex has no markdown files; physical archive appears to have happened too early"]
    return []


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    product_statuses = [file_status(repo_root, path, role="Slides product replacement test") for path in PRODUCT_SLIDES_TESTS]
    legacy_statuses = [file_status(repo_root, path, role="legacy KQ safety net") for path in LEGACY_KQ_SAFETY_NETS]
    doc_statuses = [file_status(repo_root, path, role="Slides product quality doc") for path in PRODUCT_SLIDES_DOCS]
    support_statuses = [file_status(repo_root, path, role="KR-2E support file") for path in SUPPORT_FILES]

    issues: list[str] = []
    for status in product_statuses + doc_statuses + support_statuses:
        if not status.exists:
            issues.append(f"required file missing: {status.path}")
    issues.extend(scan_positive_claims(repo_root))
    issues.extend(check_docs_codex_not_moved(repo_root))

    warnings = [f"legacy KQ safety net missing or already retired: {status.path}" for status in legacy_statuses if not status.exists]
    ready_product_tests = sum(1 for status in product_statuses if status.exists)
    ready_docs = sum(1 for status in doc_statuses if status.exists)
    return {
        "generated_at": utc_now(),
        "status": "ready" if not issues else "needs_work",
        "purpose": "KR-2E product-named Slides quality replacement coverage; no legacy KQ tests are removed.",
        "summary": {
            "product_slides_tests_required": len(PRODUCT_SLIDES_TESTS),
            "product_slides_tests_ready": ready_product_tests,
            "product_slides_docs_checked": len(PRODUCT_SLIDES_DOCS),
            "product_slides_docs_ready": ready_docs,
            "legacy_kq_safety_net_files_checked": len(LEGACY_KQ_SAFETY_NETS),
            "physical_docs_codex_archive_allowed": False,
            "physical_docs_codex_archive_blocked_until": "direct docs/codex dependencies in stage checkers/tests are rewritten or archived",
        },
        "product_slides_test_statuses": [asdict(status) for status in product_statuses],
        "legacy_kq_safety_net_statuses": [asdict(status) for status in legacy_statuses],
        "product_slides_doc_statuses": [asdict(status) for status in doc_statuses],
        "support_file_statuses": [asdict(status) for status in support_statuses],
        "issues": issues,
        "warnings": warnings,
        "next_steps": [
            "KR-2F: add first-class DOCX/PDF/XLSX workflow and quality tests.",
            "KR-3A/KR-3B: harden path portability once product replacement coverage exists.",
            "Later KR cleanup: retire legacy KQ stage tests only after product tests provide equivalent evidence.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KR-2E Slides Product Quality Replacement Coverage",
        "",
        "KR-2E adds product-named tests for accepted KQ-1A/B/C Slides quality behavior.",
        "It is additive only: legacy KQ tests and `docs/codex` remain in place.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Product Slides tests ready: `{summary['product_slides_tests_ready']}` / `{summary['product_slides_tests_required']}`",
        f"- Product Slides docs ready: `{summary['product_slides_docs_ready']}` / `{summary['product_slides_docs_checked']}`",
        f"- Legacy KQ safety net files checked: `{summary['legacy_kq_safety_net_files_checked']}`",
        f"- Physical `docs/codex` archive allowed: `{summary['physical_docs_codex_archive_allowed']}`",
        f"- Blocked until: `{summary['physical_docs_codex_archive_blocked_until']}`",
        "", "## Product Slides tests", "",
    ]
    for status in report["product_slides_test_statuses"]:
        lines.append(f"- `{status['path']}` — `{status['status']}`")
    lines += ["", "## Issues", ""]
    lines.extend([f"- {issue}" for issue in report["issues"]] or ["- None"])
    lines += ["", "## Warnings", ""]
    lines.extend([f"- {warning}" for warning in report["warnings"]] or ["- None"])
    lines += ["", "## Next steps", ""]
    lines.extend(f"- {step}" for step in report["next_steps"])
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check KR-2E Slides product quality replacement coverage.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve())
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "kr2e_slides_product_quality_replacements.json", report)
    (output_dir / "kr2e_slides_product_quality_replacements.md").write_text(render_markdown(report), encoding="utf-8")
    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())
    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-2E Slides product quality replacements: {report['status']}")
        print(f"Report written to: {output_dir}")
    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
