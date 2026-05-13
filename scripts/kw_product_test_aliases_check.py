#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MANDATORY_WORKFLOWS = ("docx", "pdf", "xlsx", "slides", "python_analysis", "browser_evidence")

REQUIRED_PRODUCT_TEST_FILES = (
    "backend/tests/workflows/test_product_workflow_aliases.py",
    "backend/tests/quality/test_product_quality_aliases.py",
    "backend/tests/integrations/test_product_path_portability_contract.py",
    "backend/tests/operators/test_product_operator_aliases.py",
)

REQUIRED_PRODUCT_DOCS = (
    "docs/product/PRODUCT_VISION.md",
    "docs/product/USER_WORKFLOWS.md",
    "docs/product/ARTIFACT_MODEL.md",
    "docs/architecture/TOOL_AND_WORKFLOW_CONTRACTS.md",
    "docs/workflows/DOCX_WORKFLOW.md",
    "docs/workflows/PDF_WORKFLOW.md",
    "docs/workflows/XLSX_WORKFLOW.md",
    "docs/workflows/SLIDES_WORKFLOW.md",
    "docs/workflows/PYTHON_ANALYSIS_WORKFLOW.md",
    "docs/workflows/BROWSER_EVIDENCE_WORKFLOW.md",
    "docs/quality/QUALITY_GATES.md",
    "docs/quality/XLSX_VALIDATION.md",
    "docs/quality/RENDER_AND_VISUAL_QA.md",
    "docs/operators/LOCAL_DEVELOPMENT.md",
)

LEGACY_BRIDGE_CHECKS = {
    "docx_pdf_ingestion": (
        "scripts/kw_docx_pdf_real_ingestion_check.py",
        "backend/app/services/docx_service/ingestion.py",
        "backend/app/services/pdf_service/ingestion.py",
    ),
    "slides_artifact_quality": (
        "scripts/kw_kq1_deck_quality_check.py",
        "scripts/kw_kq1b_exec_memo_pptx_check.py",
        "scripts/kw_kq1c_independent_render_check.py",
    ),
    "product_documentation": (
        "scripts/kw_product_docs_check.py",
        "scripts/kw_stage_docs_deprecation_check.py",
        "scripts/kw_test_inventory_product_map.py",
    ),
    "operator_readiness": (
        "scripts/kw_production_readiness_gate.py",
        "scripts/kw_full_tests_with_proxy_runner.sh",
        "scripts/kw_operator_log_archive.py",
    ),
}

PLANNED_PRODUCT_TARGETS = {
    "xlsx_runtime": {
        "status": "planned",
        "reason": "XLSX is mandatory product scope, but KR-2B only creates product-level test aliases. Runtime implementation belongs to KR-5.",
        "target_paths": (
            "backend/app/services/xlsx_service/",
            "scripts/kw_xlsx_workflow_check.py",
            "backend/tests/workflows/test_xlsx_workflow.py",
            "backend/tests/quality/test_xlsx_validation.py",
        ),
    },
    "stage_test_replacement": {
        "status": "planned",
        "reason": "Legacy stage tests remain as safety net until product workflow and quality tests prove replacement coverage.",
        "target_paths": (
            "backend/tests/workflows/",
            "backend/tests/quality/",
            "backend/tests/integrations/",
            "backend/tests/operators/",
        ),
    },
}

FORBIDDEN_PORTABILITY_MARKERS = (
    "/home/editor",
    "/home/su4ka",
    "Profile 1",
    "Profile 2",
    "profile1",
    "profile2",
    "Загрузки",
    "Downloads",
)

PORTABILITY_MARKER_CATALOG_ALLOWLIST_FILES = {
    "scripts/kw_product_test_aliases_check.py",
    "backend/tests/integrations/test_product_path_portability_contract.py",
}


@dataclass(frozen=True)
class FileCheck:
    path: str
    exists: bool
    status: str


@dataclass(frozen=True)
class BridgeCheck:
    key: str
    required_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class PortabilityCheck:
    path: str
    marker: str
    status: str


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def _file_checks(repo_root: Path, paths: tuple[str, ...]) -> list[FileCheck]:
    checks: list[FileCheck] = []
    for path in paths:
        exists = (repo_root / path).exists()
        checks.append(FileCheck(path=path, exists=exists, status="ready" if exists else "missing"))
    return checks


def _bridge_checks(repo_root: Path) -> list[BridgeCheck]:
    checks: list[BridgeCheck] = []
    for key, paths in LEGACY_BRIDGE_CHECKS.items():
        missing = tuple(path for path in paths if not (repo_root / path).exists())
        checks.append(
            BridgeCheck(
                key=key,
                required_paths=tuple(paths),
                missing_paths=missing,
                status="ready" if not missing else "missing",
            )
        )
    return checks


def _scan_portability_markers(repo_root: Path) -> list[PortabilityCheck]:
    findings: list[PortabilityCheck] = []
    candidates = [
        repo_root / "scripts/kw_product_test_aliases_check.py",
        repo_root / "backend/tests/smoke/test_product_test_aliases.py",
        repo_root / "backend/tests/workflows/test_product_workflow_aliases.py",
        repo_root / "backend/tests/quality/test_product_quality_aliases.py",
        repo_root / "backend/tests/integrations/test_product_path_portability_contract.py",
        repo_root / "backend/tests/operators/test_product_operator_aliases.py",
        repo_root / "docs/refactor/PRODUCT_TEST_ALIASES.md",
    ]
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if rel in PORTABILITY_MARKER_CATALOG_ALLOWLIST_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_PORTABILITY_MARKERS:
            if marker in text:
                findings.append(PortabilityCheck(path=rel, marker=marker, status="blocked"))
    return findings


def build_product_test_aliases_report(repo_root: Path) -> dict[str, Any]:
    product_test_checks = _file_checks(repo_root, REQUIRED_PRODUCT_TEST_FILES)
    product_doc_checks = _file_checks(repo_root, REQUIRED_PRODUCT_DOCS)
    bridge_checks = _bridge_checks(repo_root)
    portability_findings = _scan_portability_markers(repo_root)

    missing_product_tests = [check.path for check in product_test_checks if not check.exists]
    missing_product_docs = [check.path for check in product_doc_checks if not check.exists]
    missing_legacy_bridges = {
        check.key: list(check.missing_paths) for check in bridge_checks if check.missing_paths
    }

    issues: list[str] = []
    for path in missing_product_tests:
        issues.append(f"missing product test alias: {path}")
    for path in missing_product_docs:
        issues.append(f"missing canonical product doc: {path}")
    for key, paths in missing_legacy_bridges.items():
        issues.append(f"legacy bridge {key} is missing required paths: {', '.join(paths)}")
    for finding in portability_findings:
        issues.append(f"non-portable marker {finding.marker!r} found in {finding.path}")

    physical_archive_blocked = True
    status = "ready" if not issues else "blocked"
    return {
        "status": status,
        "issues": issues,
        "mandatory_workflows": list(MANDATORY_WORKFLOWS),
        "product_test_aliases_ready": not missing_product_tests,
        "product_docs_ready": not missing_product_docs,
        "legacy_bridge_aliases_ready": not missing_legacy_bridges,
        "path_portability_ready_for_new_aliases": not portability_findings,
        "physical_docs_archive_blocked": physical_archive_blocked,
        "blocked_until": "KR-2B/KR-2C replacement coverage is accepted and legacy checker scripts no longer read docs/codex directly.",
        "product_test_checks": [asdict(check) for check in product_test_checks],
        "product_doc_checks": [asdict(check) for check in product_doc_checks],
        "legacy_bridge_checks": [asdict(check) for check in bridge_checks],
        "portability_findings": [asdict(finding) for finding in portability_findings],
        "planned_product_targets": PLANNED_PRODUCT_TARGETS,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "kr2b_product_test_aliases_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# KR-2B Product Test Aliases Report",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Mandatory workflows",
        "",
    ]
    for workflow in report["mandatory_workflows"]:
        lines.append(f"- `{workflow}`")
    lines.extend(
        [
            "",
            "## Product test alias readiness",
            "",
            f"- product_test_aliases_ready: `{report['product_test_aliases_ready']}`",
            f"- product_docs_ready: `{report['product_docs_ready']}`",
            f"- legacy_bridge_aliases_ready: `{report['legacy_bridge_aliases_ready']}`",
            f"- path_portability_ready_for_new_aliases: `{report['path_portability_ready_for_new_aliases']}`",
            f"- physical_docs_archive_blocked: `{report['physical_docs_archive_blocked']}`",
            "",
            "## Product test files",
            "",
        ]
    )
    for check in report["product_test_checks"]:
        lines.append(f"- `{check['path']}`: {check['status']}")
    lines.extend(["", "## Legacy bridge checks", ""])
    for check in report["legacy_bridge_checks"]:
        missing = ", ".join(check["missing_paths"]) or "none"
        lines.append(f"- `{check['key']}`: {check['status']} (missing: {missing})")
    lines.extend(["", "## Planned product targets", ""])
    for key, payload in report["planned_product_targets"].items():
        lines.append(f"### {key}")
        lines.append("")
        lines.append(f"Status: `{payload['status']}`")
        lines.append("")
        lines.append(payload["reason"])
        lines.append("")
        for path in payload["target_paths"]:
            lines.append(f"- `{path}`")
        lines.append("")
    if report["issues"]:
        lines.extend(["## Issues", ""])
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    (output_dir / "kr2b_product_test_aliases_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def zip_dir(source_dir: Path, zip_out: Path) -> None:
    zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KR-2B product-level test aliases.")
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_script())
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--zip-out", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = build_product_test_aliases_report(repo_root)
    if args.output_dir:
        write_report(report, args.output_dir)
        if args.zip_out:
            zip_dir(args.output_dir, args.zip_out)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"KR-2B product test aliases status: {report['status']}")
    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
