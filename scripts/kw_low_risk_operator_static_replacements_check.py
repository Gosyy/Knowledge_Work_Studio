#!/usr/bin/env python3
"""KR-2D low-risk operator/static replacement coverage check.

This checker is intentionally additive and read-only. It verifies that product-level
operator/static tests now cover the first low-risk replacement areas before any
legacy stage tests or docs/codex files are removed.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOW_RISK_PRODUCT_TESTS: tuple[str, ...] = (
    "backend/tests/operators/test_log_archive_product_contract.py",
    "backend/tests/operators/test_product_docs_operator_contract.py",
    "backend/tests/operators/test_cleanup_audit_operator_contract.py",
    "backend/tests/operators/test_stage_dependency_inventory_operator_contract.py",
)

LOW_RISK_SUPPORT_FILES: tuple[str, ...] = (
    "scripts/kw_low_risk_operator_static_replacements_check.py",
    "docs/refactor/LOW_RISK_OPERATOR_STATIC_REPLACEMENT_TESTS.md",
)

LEGACY_SAFETY_NET_FILES: tuple[str, ...] = (
    "backend/tests/smoke/test_operator_logging_downloads_policy.py",
    "scripts/kw_operator_logging_policy_check.py",
    "backend/tests/smoke/test_repository_cleanup_audit.py",
    "backend/tests/smoke/test_stage_checker_dependency_inventory.py",
)

CANONICAL_PRODUCT_DOCS: tuple[str, ...] = (
    "docs/product/PRODUCT_VISION.md",
    "docs/product/USER_WORKFLOWS.md",
    "docs/product/ARTIFACT_MODEL.md",
    "docs/workflows/DOCX_WORKFLOW.md",
    "docs/workflows/PDF_WORKFLOW.md",
    "docs/workflows/XLSX_WORKFLOW.md",
    "docs/workflows/SLIDES_WORKFLOW.md",
    "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
    "docs/quality/QUALITY_GATES.md",
)

FORBIDDEN_PRODUCT_TEST_MARKERS: tuple[str, ...] = (
    "/home/editor",
    "/home/su4ka",
    "Profile 1",
    "Profile 2",
    "profile1",
    "profile2",
    "Загрузки",
    "Downloads",
)


@dataclass(frozen=True)
class FileStatus:
    path: str
    exists: bool
    status: str
    reason: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_file_exists(repo_root: Path, path: str, *, role: str) -> FileStatus:
    exists = (repo_root / path).exists()
    return FileStatus(
        path=path,
        exists=exists,
        status="ready" if exists else "missing",
        reason=f"{role} {'exists' if exists else 'is missing'}",
    )


def scan_product_tests_for_path_markers(repo_root: Path) -> list[str]:
    issues: list[str] = []
    intentional_marker_catalog_files = {
        "backend/tests/operators/test_product_docs_operator_contract.py",
    }
    for rel_path in LOW_RISK_PRODUCT_TESTS:
        path = repo_root / rel_path
        if not path.exists():
            continue

        # Some product tests intentionally contain marker catalogs such as
        # "/home/editor", "/home/su4ka", "Profile 1", or "Загрузки" because
        # they verify that active product documentation does not depend on those
        # machine-local examples. Treat those catalogs as test fixtures, not as
        # path dependencies.
        if rel_path in intentional_marker_catalog_files:
            continue

        text = _read_text(path)
        for marker in FORBIDDEN_PRODUCT_TEST_MARKERS:
            if marker in text:
                issues.append(f"{rel_path}: contains non-portable marker {marker!r}")
    return issues


def check_docs_codex_not_moved(repo_root: Path) -> list[str]:
    """KR-2D must not physically move legacy docs/codex yet."""
    codex_dir = repo_root / "docs" / "codex"
    if not codex_dir.exists():
        return ["docs/codex is missing; physical archive is still blocked until stage checkers are rewritten"]
    if not any(codex_dir.glob("*.md")):
        return ["docs/codex contains no markdown files; physical archive appears to have happened too early"]
    return []


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()

    product_test_statuses = [
        check_file_exists(repo_root, path, role="low-risk product replacement test")
        for path in LOW_RISK_PRODUCT_TESTS
    ]
    support_statuses = [
        check_file_exists(repo_root, path, role="KR-2D support file")
        for path in LOW_RISK_SUPPORT_FILES
    ]
    legacy_statuses = [
        check_file_exists(repo_root, path, role="legacy safety net")
        for path in LEGACY_SAFETY_NET_FILES
    ]
    docs_statuses = [
        check_file_exists(repo_root, path, role="canonical product doc")
        for path in CANONICAL_PRODUCT_DOCS
    ]

    issues: list[str] = []
    for status in product_test_statuses + support_statuses + docs_statuses:
        if not status.exists:
            issues.append(f"required file missing: {status.path}")

    issues.extend(scan_product_tests_for_path_markers(repo_root))
    issues.extend(check_docs_codex_not_moved(repo_root))

    # Legacy safety net files are intentionally checked but not required forever.
    # If one is missing, this is not a failure by itself; it means a later cleanup
    # already retired it and should have product replacement evidence.
    warnings = [
        f"legacy safety net missing or already retired: {status.path}"
        for status in legacy_statuses
        if not status.exists
    ]

    ready_product_tests = sum(1 for status in product_test_statuses if status.exists)
    ready_docs = sum(1 for status in docs_statuses if status.exists)

    payload: dict[str, Any] = {
        "generated_at": utc_now(),
        "status": "ready" if not issues else "needs_work",
        "purpose": "KR-2D low-risk operator/static replacement coverage check; no legacy tests or docs/codex files are removed.",
        "summary": {
            "product_replacement_tests_required": len(LOW_RISK_PRODUCT_TESTS),
            "product_replacement_tests_ready": ready_product_tests,
            "canonical_product_docs_checked": len(CANONICAL_PRODUCT_DOCS),
            "canonical_product_docs_ready": ready_docs,
            "legacy_safety_net_files_checked": len(LEGACY_SAFETY_NET_FILES),
            "physical_docs_codex_archive_allowed": False,
            "physical_docs_codex_archive_blocked_until": "stage checker/test direct docs/codex dependencies are rewritten or archived",
        },
        "product_test_statuses": [asdict(status) for status in product_test_statuses],
        "support_file_statuses": [asdict(status) for status in support_statuses],
        "legacy_safety_net_statuses": [asdict(status) for status in legacy_statuses],
        "canonical_product_doc_statuses": [asdict(status) for status in docs_statuses],
        "issues": issues,
        "warnings": warnings,
        "next_steps": [
            "KR-2E: rename KQ-1A/B/C slide quality behavior into product quality tests.",
            "KR-2F: add first-class DOCX/PDF/XLSX workflow tests before retiring related RF/P/S stage tests.",
            "KR-3A/KR-3B: harden path portability after product replacement coverage exists.",
        ],
    }
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KR-2D Low-Risk Operator/Static Replacement Coverage",
        "",
        "KR-2D is the first small replacement step after KR-2C.",
        "It adds product-level tests around low-risk operator/static areas while keeping legacy stage tests as a safety net.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Product replacement tests ready: `{summary['product_replacement_tests_ready']}` / `{summary['product_replacement_tests_required']}`",
        f"- Canonical product docs ready: `{summary['canonical_product_docs_ready']}` / `{summary['canonical_product_docs_checked']}`",
        f"- Legacy safety net files checked: `{summary['legacy_safety_net_files_checked']}`",
        f"- Physical `docs/codex` archive allowed: `{summary['physical_docs_codex_archive_allowed']}`",
        f"- Blocked until: `{summary['physical_docs_codex_archive_blocked_until']}`",
        "",
        "## Product replacement tests",
        "",
    ]
    for status in report["product_test_statuses"]:
        lines.append(f"- `{status['path']}` — `{status['status']}`")
    lines += ["", "## Issues", ""]
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- None")
    lines += ["", "## Warnings", ""]
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")
    lines += ["", "## Next steps", ""]
    for step in report["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check KR-2D low-risk operator/static replacement coverage.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "kr2d_low_risk_operator_static_replacements.json", report)
    (output_dir / "kr2d_low_risk_operator_static_replacements.md").write_text(
        render_markdown(report),
        encoding="utf-8",
    )

    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-2D low-risk operator/static replacements: {report['status']}")
        print(f"Report written to: {output_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
