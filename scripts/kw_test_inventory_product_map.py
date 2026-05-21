#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE_TEST_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"test_s\d+[a-z]?_", "slides_or_selected_benchmark_stage"),
    (r"test_p\d+(_|[a-z])", "release_hardening_stage"),
    (r"test_p10_", "post_review_release_stage"),
    (r"test_rc\d+_", "release_candidate_stage"),
    (r"test_rch\d+_", "release_candidate_hotfix_stage"),
    (r"test_rf\d+", "runtime_foundation_stage"),
    (r"test_kq\d+", "quality_phase_stage"),
    (r"test_k\d+_", "k_phase_stage"),
    (r"test_krc_", "k_release_closure_stage"),
)

STAGE_SCRIPT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"kw_s\d+[a-z]?_", "slides_or_selected_benchmark_stage_checker"),
    (r"kw_p\d+_", "release_hardening_stage_checker"),
    (r"kw_p10_", "post_review_release_stage_checker"),
    (r"kw_rc\d+_", "release_candidate_stage_checker"),
    (r"kw_rch\d+_", "release_candidate_hotfix_stage_checker"),
    (r"kw_rf", "runtime_foundation_stage_checker"),
    (r"kw_kq\d+", "quality_phase_stage_checker"),
    (r"kw_k\d+_", "k_phase_stage_checker"),
    (r"kw_krc_", "k_release_closure_stage_checker"),
)

PRODUCT_TEST_TARGETS: dict[str, list[str]] = {
    "api": [
        "backend/tests/api/test_health_ready.py",
        "backend/tests/api/test_sessions_uploads_tasks_artifacts.py",
        "backend/tests/api/test_artifact_download.py",
    ],
    "workflows": [
        "backend/tests/workflows/test_docx_workflow.py",
        "backend/tests/workflows/test_pdf_workflow.py",
        "backend/tests/workflows/test_xlsx_workflow.py",
        "backend/tests/workflows/test_slides_workflow.py",
        "backend/tests/workflows/test_python_analysis_workflow.py",
        "backend/tests/workflows/test_browser_evidence_workflow.py",
    ],
    "quality": [
        "backend/tests/quality/test_artifact_bundle_contract.py",
        "backend/tests/quality/test_provenance_manifest.py",
        "backend/tests/quality/test_pptx_render_qa.py",
        "backend/tests/quality/test_xlsx_validation.py",
        "backend/tests/quality/test_source_grounding.py",
    ],
    "integrations": [
        "backend/tests/integrations/test_storage_portability.py",
        "backend/tests/integrations/test_metadata_backend_selection.py",
        "backend/tests/integrations/test_database_bootstrap.py",
        "backend/tests/integrations/test_local_file_storage.py",
    ],
    "operators": [
        "backend/tests/operators/test_env_validation.py",
        "backend/tests/operators/test_production_readiness_gate.py",
        "backend/tests/operators/test_log_archive.py",
        "backend/tests/operators/test_cleanup_audit_tools.py",
    ],
}

PRODUCT_SCRIPT_TARGETS: dict[str, list[str]] = {
    "workflow_checks": [
        "scripts/kw_workflow_contracts_check.py",
        "scripts/kw_product_docs_check.py",
    ],
    "quality_checks": [
        "scripts/kw_artifact_bundle_quality_check.py",
        "scripts/kw_slides_render_qa_check.py",
        "scripts/kw_xlsx_validation_check.py",
    ],
    "operator_checks": [
        "scripts/kw_production_readiness_gate.py",
        "scripts/kw_operator_log_archive.py",
        "scripts/kw_repo_cleanup_audit.py",
        "scripts/kw_repo_cleanup_policy.py",
        "scripts/kw_stage_docs_deprecation_check.py",
    ],
}

REWRITE_TARGET_HINTS: tuple[tuple[str, str], ...] = (
    ("test_kq1_deck_quality.py", "backend/tests/quality/test_artifact_bundle_contract.py"),
    ("test_kq1b_exec_memo_deck_generation.py", "backend/tests/workflows/test_slides_workflow.py"),
    ("test_kq1c_independent_render_qa.py", "backend/tests/quality/test_pptx_render_qa.py"),
    ("test_rf3_docx_pdf_real_ingestion.py", "backend/tests/workflows/test_docx_workflow.py + backend/tests/workflows/test_pdf_workflow.py"),
    ("test_s7_offline_research_citations.py", "backend/tests/quality/test_source_grounding.py"),
    ("test_s8_conversational_edit_loop.py", "backend/tests/workflows/test_slides_workflow.py"),
    ("test_s9_render_based_visual_qa.py", "backend/tests/quality/test_pptx_render_qa.py"),
    ("test_operator_logging_downloads_policy.py", "backend/tests/operators/test_log_archive.py"),
)


@dataclass(frozen=True)
class InventoryItem:
    path: str
    recommendation: str = "unknown"
    reason: str = ""


@dataclass(frozen=True)
class Decision:
    path: str
    item_type: str
    action: str
    category: str
    reason: str
    rewrite_target: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json_from_zip(zip_path: Path, name: str, default: Any) -> Any:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            return json.loads(zf.read(name).decode("utf-8"))
    except KeyError:
        return default


def load_audit_zip(zip_path: Path) -> dict[str, Any]:
    return {
        "tests_inventory": read_json_from_zip(zip_path, "test_inventory.json", []),
        "scripts_inventory": read_json_from_zip(zip_path, "scripts_inventory.json", []),
        "portability_findings": read_json_from_zip(zip_path, "path_portability_findings.json", []),
        "workflow_coverage": read_json_from_zip(zip_path, "workflow_coverage.json", []),
        "cleanup_inventory": read_json_from_zip(zip_path, "cleanup_inventory.json", {}),
    }


def build_inventory_from_repo(repo_root: Path) -> dict[str, Any]:
    tests = [
        {"path": path.relative_to(repo_root).as_posix(), "recommendation": "scan_only", "reason": "discovered from repo tree"}
        for path in sorted((repo_root / "backend" / "tests").rglob("test_*.py"))
        if path.is_file()
    ]
    scripts = [
        {"path": path.relative_to(repo_root).as_posix(), "recommendation": "scan_only", "reason": "discovered from repo tree"}
        for path in sorted((repo_root / "scripts").glob("kw_*.py"))
        if path.is_file()
    ]
    return {
        "tests_inventory": tests,
        "scripts_inventory": scripts,
        "portability_findings": [],
        "workflow_coverage": [],
        "cleanup_inventory": {},
    }


def basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def first_matching_stage(path: str, patterns: tuple[tuple[str, str], ...]) -> str | None:
    name = basename(path)
    for pattern, category in patterns:
        if re.search(pattern, name):
            return category
    return None


def rewrite_target_for_test(path: str) -> str | None:
    name = basename(path)
    for marker, target in REWRITE_TARGET_HINTS:
        if marker == name:
            return target
    if "docx" in name:
        return "backend/tests/workflows/test_docx_workflow.py"
    if "pdf" in name:
        return "backend/tests/workflows/test_pdf_workflow.py"
    if "xlsx" in name or "sheet" in name or "excel" in name:
        return "backend/tests/workflows/test_xlsx_workflow.py"
    if "slide" in name or "deck" in name or "pptx" in name:
        return "backend/tests/workflows/test_slides_workflow.py or backend/tests/quality/test_pptx_render_qa.py"
    if "provenance" in name or "citation" in name or "source" in name:
        return "backend/tests/quality/test_provenance_manifest.py or backend/tests/quality/test_source_grounding.py"
    if "operator" in name or "readiness" in name or "log" in name:
        return "backend/tests/operators/test_production_readiness_gate.py or backend/tests/operators/test_log_archive.py"
    return None


def classify_test(raw: dict[str, Any]) -> Decision:
    path = str(raw.get("path", ""))
    rec = str(raw.get("recommendation", ""))
    reason = str(raw.get("reason", ""))
    name = basename(path)
    stage_category = first_matching_stage(path, STAGE_TEST_PATTERNS)

    if name == "__init__.py":
        return Decision(path, "test", "keep", "package_marker", "package marker")

    if "backend/tests/api/" in path or "backend/tests/services/" in path:
        return Decision(path, "test", "keep", "product_or_service_test", "API/service test already describes product behavior")

    if any(part in path for part in ("test_repository_cleanup_", "test_product_documentation_", "test_stage_documentation_")):
        return Decision(path, "test", "keep_temporarily", "kr_refactor_tooling", "KR audit/deprecation tests are needed during cleanup")

    if name in {"test_operator_logging_downloads_policy.py"}:
        return Decision(path, "test", "rewrite", "operator_product_test", "operator behavior should move to product operator test naming", rewrite_target_for_test(path))

    if stage_category:
        target = rewrite_target_for_test(path)
        action = "rewrite" if target else "archive_after_replacement"
        return Decision(path, "test", action, stage_category, "stage-specific test name/content should not be active long-term", target)

    if "smoke" in path:
        return Decision(path, "test", "review", "smoke_test", "smoke test may stay if renamed around product behavior")

    return Decision(path, "test", "keep", "product_or_layer_test", rec or reason or "appears product-oriented")


def classify_script(raw: dict[str, Any]) -> Decision:
    path = str(raw.get("path", ""))
    rec = str(raw.get("recommendation", ""))
    reason = str(raw.get("reason", ""))
    name = basename(path)
    stage_category = first_matching_stage(path, STAGE_SCRIPT_PATTERNS)

    if name in {
        "kw_production_readiness_gate.py",
        "kw_operator_log_archive.py",
        "kw_full_tests_with_proxy_runner.sh",
        "kw_repo_cleanup_audit.py",
        "kw_repo_cleanup_policy.py",
        "kw_stage_docs_deprecation_check.py",
        "kw_product_docs_check.py",
    }:
        return Decision(path, "script", "keep", "operator_or_kr_tool", "current operator/KR tool")

    if stage_category:
        target = None
        if "kq1" in name or "pptx" in name or "deck" in name or "slides" in name:
            target = "scripts/kw_slides_quality_check.py or scripts/kw_artifact_bundle_quality_check.py"
        elif "docx" in name or "pdf" in name:
            target = "scripts/kw_docx_pdf_workflow_check.py"
        return Decision(path, "script", "rewrite_or_archive", stage_category, "stage-specific checker should become product checker or archive after replacement", target)

    if name.endswith("_check.py"):
        return Decision(path, "script", "review", "operator_check", rec or reason or "check script may be product-level")

    return Decision(path, "script", "keep_or_review", "script", rec or reason or "script discovered by audit")


def summarize_decisions(decisions: list[Decision]) -> dict[str, Any]:
    by_action: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for decision in decisions:
        by_action[decision.action] = by_action.get(decision.action, 0) + 1
        by_category[decision.category] = by_category.get(decision.category, 0) + 1
    return {
        "total": len(decisions),
        "by_action": dict(sorted(by_action.items())),
        "by_category": dict(sorted(by_category.items())),
    }


def product_target_status(existing_tests: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group, targets in PRODUCT_TEST_TARGETS.items():
        for target in targets:
            rows.append({
                "group": group,
                "path": target,
                "exists_now": target in existing_tests,
                "status": "present" if target in existing_tests else "planned",
            })
    return rows


def build_report(audit: dict[str, Any]) -> dict[str, Any]:
    tests_raw = list(audit.get("tests_inventory") or [])
    scripts_raw = list(audit.get("scripts_inventory") or [])
    test_decisions = [classify_test(item) for item in tests_raw]
    script_decisions = [classify_script(item) for item in scripts_raw]
    existing_tests = {str(item.get("path", "")) for item in tests_raw}

    stage_test_count = sum(1 for d in test_decisions if d.action in {"rewrite", "archive_after_replacement"})
    stage_script_count = sum(1 for d in script_decisions if d.action == "rewrite_or_archive")
    physical_archive_blockers = [
        asdict(d)
        for d in test_decisions + script_decisions
        if d.action in {"rewrite", "archive_after_replacement", "rewrite_or_archive"}
    ]

    required_groups = set(PRODUCT_TEST_TARGETS)
    target_rows = product_target_status(existing_tests)
    groups_with_targets = {row["group"] for row in target_rows}
    missing_groups = sorted(required_groups - groups_with_targets)

    status = "ready" if not missing_groups else "needs_attention"
    return {
        "generated_at": utc_now(),
        "status": status,
        "purpose": "KR-2A test inventory and product test map; no files are deleted or moved.",
        "summary": {
            "tests_total": len(test_decisions),
            "scripts_total": len(script_decisions),
            "stage_tests_rewrite_or_archive_count": stage_test_count,
            "stage_scripts_rewrite_or_archive_count": stage_script_count,
            "physical_docs_archive_blocked": bool(physical_archive_blockers),
            "physical_docs_archive_blocked_until": "KR-2B/KR-2C rewrite or archive stage-specific tests/checker scripts",
        },
        "test_decisions": [asdict(d) for d in sorted(test_decisions, key=lambda d: d.path)],
        "script_decisions": [asdict(d) for d in sorted(script_decisions, key=lambda d: d.path)],
        "product_test_targets": PRODUCT_TEST_TARGETS,
        "product_script_targets": PRODUCT_SCRIPT_TARGETS,
        "product_test_target_status": target_rows,
        "physical_archive_blockers": physical_archive_blockers,
        "decision_summaries": {
            "tests": summarize_decisions(test_decisions),
            "scripts": summarize_decisions(script_decisions),
        },
        "next_steps": [
            "KR-2B: create/rename product quality and workflow tests around DOCX/PDF/XLSX/Slides/Python/Browser.",
            "KR-2C: retire or archive stage-specific smoke tests after product replacements pass.",
            "KR-3A/KR-3B: neutralize hardcoded profile/path/branch/commit assumptions.",
            "Revisit physical docs/codex archive only after stage checker dependencies are gone.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    test_actions = report["decision_summaries"]["tests"]["by_action"]
    script_actions = report["decision_summaries"]["scripts"]["by_action"]
    lines = [
        "# KR-2A Test Inventory and Product Test Map",
        "",
        "KR-2A is an inventory and planning step. It does not delete, move, or rename tests.",
        "Its job is to explain which tests/checker scripts describe the product and which ones still describe development stages.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Tests scanned: `{summary['tests_total']}`",
        f"- Scripts scanned: `{summary['scripts_total']}`",
        f"- Stage tests to rewrite/archive later: `{summary['stage_tests_rewrite_or_archive_count']}`",
        f"- Stage scripts to rewrite/archive later: `{summary['stage_scripts_rewrite_or_archive_count']}`",
        f"- Physical `docs/codex` archive blocked: `{summary['physical_docs_archive_blocked']}`",
        f"- Blocked until: `{summary['physical_docs_archive_blocked_until']}`",
        "",
        "## Test actions",
        "",
    ]
    for action, count in sorted(test_actions.items()):
        lines.append(f"- `{action}`: {count}")
    lines += ["", "## Script actions", ""]
    for action, count in sorted(script_actions.items()):
        lines.append(f"- `{action}`: {count}")

    lines += [
        "",
        "## Required product test target tree",
        "",
    ]
    for group, targets in PRODUCT_TEST_TARGETS.items():
        lines.append(f"### {group}")
        lines.append("")
        for target in targets:
            lines.append(f"- `{target}`")
        lines.append("")

    blockers = report.get("physical_archive_blockers", [])[:40]
    lines += [
        "## First physical-archive blockers",
        "",
        "These stage-specific tests/scripts should be rewritten or retired before moving `docs/codex` files.",
        "",
    ]
    for item in blockers:
        target = f" → `{item['rewrite_target']}`" if item.get("rewrite_target") else ""
        lines.append(f"- `{item['path']}` — `{item['action']}` / `{item['category']}`{target}")
    if len(report.get("physical_archive_blockers", [])) > len(blockers):
        lines.append(f"- ... plus {len(report['physical_archive_blockers']) - len(blockers)} more entries in JSON.")

    lines += ["", "## Next steps", ""]
    for step in report.get("next_steps", []):
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build KR-2A test inventory and product test map.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--audit-zip", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if args.audit_zip:
        audit = load_audit_zip(args.audit_zip.resolve())
    else:
        audit = build_inventory_from_repo(repo_root)

    report = build_report(audit)
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "kr2a_test_inventory_product_map.json", report)
    write_json(out_dir / "kr2a_test_decisions.json", report["test_decisions"])
    write_json(out_dir / "kr2a_script_decisions.json", report["script_decisions"])
    write_json(out_dir / "kr2a_product_test_targets.json", report["product_test_targets"])
    write_json(out_dir / "kr2a_physical_archive_blockers.json", report["physical_archive_blockers"])
    (out_dir / "kr2a_test_inventory_product_map.md").write_text(render_markdown(report), encoding="utf-8")

    if args.zip_out:
        write_zip(out_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({
            "status": report["status"],
            "tests_total": report["summary"]["tests_total"],
            "scripts_total": report["summary"]["scripts_total"],
            "stage_tests_rewrite_or_archive_count": report["summary"]["stage_tests_rewrite_or_archive_count"],
            "stage_scripts_rewrite_or_archive_count": report["summary"]["stage_scripts_rewrite_or_archive_count"],
            "physical_docs_archive_blocked": report["summary"]["physical_docs_archive_blocked"],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"KR-2A test inventory product map: {report['status']}")
        print(f"Report written to: {out_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
