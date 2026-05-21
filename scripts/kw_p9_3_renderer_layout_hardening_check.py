#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

P9_3_CHECKPOINT = "P9-3"
P9_3_SCHEMA_VERSION = "p9.3.renderer_layout_hardening.v1"
P9_BRANCH = "9_Product_Release_Hardening"
P9_2_ACCEPT_COMMIT = "36bd460f605ad9dec532825f1820983657ebe5d4"
GOLDEN_CASES_PATH = "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json"
REQUIRED_FILES = (
    "backend/app/services/k_phase/renderer_quality.py",
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_p9_2_renderer_content_hardening_check.py",
    "backend/tests/smoke/test_p9_2_renderer_content_hardening.py",
    "scripts/kw_p9_3_renderer_layout_hardening_check.py",
    "backend/tests/smoke/test_p9_3_renderer_layout_hardening.py",
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md",
    "docs/codex/P9_3_RENDERER_LAYOUT_HARDENING.md",
)
BANNED_LABELS = ("Current / Option A", "Target / Option B", "RCH1 structured data summary")
NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_p9_3": False,
    "db_schema_migration_added_by_p9_3": False,
    "frontend_runtime_changed_by_p9_3": False,
    "dependency_versions_changed_by_p9_3": False,
    "dockerfiles_changed_by_p9_3": False,
    "cloud_llm_added_by_p9_3": False,
    "cloud_vision_added_by_p9_3": False,
    "kimi_level_claimed_by_p9_3": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class RendererProbe:
    case_id: str
    slide_count: int
    layout_hints: tuple[str, ...]
    comparison_titles: tuple[str, ...]
    table_columns: tuple[tuple[str, ...], ...]
    banned_labels_removed: bool
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def load_json(repo_root: Path, rel: str) -> Any:
    return json.loads((repo_root / rel).read_text(encoding="utf-8"))


def golden_cases(repo_root: Path) -> list[dict[str, Any]]:
    payload = load_json(repo_root, GOLDEN_CASES_PATH)
    return payload if isinstance(payload, list) else list(payload.get("cases", []))


def case_by_id(cases: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for case in cases:
        if case.get("case_id") == case_id:
            return case
    raise KeyError(case_id)


def text_has_banned_label(text: str) -> bool:
    lowered = text.lower()
    if "\nreview\n" in f"\n{lowered}\n":
        return True
    return any(label.lower() in lowered for label in BANNED_LABELS)


def block_text(block: Any) -> str:
    parts: list[str] = []
    for attr in ("left_title", "right_title", "caption"):
        value = getattr(block, attr, None)
        if value:
            parts.append(str(value))
    columns = getattr(block, "columns", ())
    rows = getattr(block, "rows", ())
    parts.extend(str(column) for column in columns)
    parts.extend(str(cell) for row in rows for cell in row)
    left_items = getattr(block, "left_items", ())
    right_items = getattr(block, "right_items", ())
    parts.extend(str(item) for item in left_items)
    parts.extend(str(item) for item in right_items)
    return "\n".join(parts)


def build_plan(case: dict[str, Any]) -> Any:
    from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine

    request = K1PlanningRequest(
        source_text=str(case["source_text"]),
        audience=str(case.get("audience") or "operator_review"),
        deck_goal=str(case.get("deck_goal") or "Create a source-grounded presentation plan."),
        target_slide_count=int(case.get("target_slide_count") or 7),
        source_refs=({"source_id": str(case.get("case_id") or "golden_case"), "title": str(case.get("title") or "Golden case")},),
    )
    return LocalGigaChatPlanningEngine(None).plan(request).plan


def render_plan(plan: Any) -> tuple[Any, dict[str, Any]]:
    from backend.app.services.k_phase.renderer_quality import improve_presentation_plan_render_quality

    result = improve_presentation_plan_render_quality(plan)
    return result.render_plan, dict(result.safe_metadata)


def evaluate_cases(repo_root: Path) -> tuple[list[RendererProbe], list[str]]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.slides_service.blocks import ComparisonBlock, TableBlock
    from backend.app.services.slides_service.outline import SlideType

    errors: list[str] = []
    cases = golden_cases(repo_root)
    required_case_ids = ("k0_comparison_table_to_decision_deck", "k0_arch_doc_to_architecture_deck", "k0_project_log_to_status_deck", "k0_long_docx_pdf_to_structured_presentation")
    probes: list[RendererProbe] = []

    for case_id in required_case_ids:
        plan = build_plan(case_by_id(cases, case_id))
        rendered, metadata = render_plan(plan)
        all_block_text = "\n".join(block_text(block) for slide in rendered.slides for block in slide.blocks)
        banned_removed = not text_has_banned_label(all_block_text)
        if not banned_removed:
            errors.append(f"{case_id}: renderer still emitted generic Current/Target or Review labels")
        if metadata.get("p9_3_renderer_layout_hardening_supported") is not True:
            errors.append(f"{case_id}: P9-3 renderer metadata flag missing")
        if metadata.get("p9_3_arbitrary_current_target_labels_removed") is not True:
            errors.append(f"{case_id}: P9-3 current/target metadata flag missing")
        if metadata.get("p9_3_generic_review_placeholder_removed") is not True:
            errors.append(f"{case_id}: P9-3 review-placeholder metadata flag missing")
        comparison_titles: list[str] = []
        table_columns: list[tuple[str, ...]] = []
        for slide in rendered.slides:
            for block in slide.blocks:
                if isinstance(block, ComparisonBlock):
                    comparison_titles.extend([block.left_title, block.right_title])
                if isinstance(block, TableBlock):
                    table_columns.append(tuple(block.columns))
        probes.append(
            RendererProbe(
                case_id=case_id,
                slide_count=len(rendered.slides),
                layout_hints=tuple(str(slide.layout_hint) for slide in rendered.slides),
                comparison_titles=tuple(comparison_titles),
                table_columns=tuple(table_columns),
                banned_labels_removed=banned_removed,
                notes=(f"metadata_schema={metadata.get('p9_3_schema_version')}",),
            )
        )
        if case_id == "k0_comparison_table_to_decision_deck":
            title_slide = rendered.slides[0]
            if title_slide.slide_type is not SlideType.TITLE or title_slide.layout_hint not in {"title_slide", "title_with_visual"}:
                errors.append(f"comparison table title slide was not preserved as title layout: {title_slide.layout_hint}")
            decision_slide = next((slide for slide in rendered.slides if "Decision matrix" in slide.title), None)
            if decision_slide is None:
                errors.append("comparison table renderer lost decision matrix slide")
            else:
                comparison = next((block for block in decision_slide.blocks if isinstance(block, ComparisonBlock)), None)
                if comparison is None:
                    errors.append("decision matrix slide did not render a comparison block")
                else:
                    if comparison.left_title != "Runtime options" or comparison.right_title != "Decision criteria":
                        errors.append("decision matrix comparison titles are not case-aware")
                    for expected in ("Direct local GigaChat", "LiteLLM gateway", "Cloud LLM"):
                        if expected not in comparison.left_items:
                            errors.append(f"decision matrix options missing {expected}")
            evidence_slide = next((slide for slide in rendered.slides if "LiteLLM gateway" in slide.title), None)
            if evidence_slide is None:
                errors.append("comparison table renderer lost LiteLLM evidence slide")
            else:
                table = next((block for block in evidence_slide.blocks if isinstance(block, TableBlock)), None)
                if table is None:
                    errors.append("LiteLLM evidence slide did not render a data table")
                elif table.columns != ("Dimension", "Evidence", "Operator use"):
                    errors.append(f"LiteLLM evidence table columns are not P9-3 columns: {table.columns}")

    return probes, errors


def production_gate_errors(repo_root: Path) -> list[str]:
    gate = repo_root / "scripts/kw_production_readiness_gate.py"
    if not gate.exists():
        return ["missing production readiness gate"]
    text = gate.read_text(encoding="utf-8")
    errors: list[str] = []
    for rel in (
        "docs/codex/P9_3_RENDERER_LAYOUT_HARDENING.md",
        "scripts/kw_p9_3_renderer_layout_hardening_check.py",
        "backend/tests/smoke/test_p9_3_renderer_layout_hardening.py",
    ):
        if rel not in text:
            errors.append(f"production readiness gate does not require P9-3 file: {rel}")
    if "P9-3 Renderer/layout hardening" not in text:
        errors.append("production readiness gate does not execute P9-3 checker")
    return errors


def static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-3 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    if require_ready and branch not in (P9_BRANCH, "unknown"):
        errors.append(f"expected branch {P9_BRANCH}, got {branch}")
    return errors


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    errors.extend(static_errors(repo_root, require_ready))
    probes: list[RendererProbe] = []
    if not errors:
        probes, runtime_errors = evaluate_cases(repo_root)
        errors.extend(runtime_errors)
    errors.extend(production_gate_errors(repo_root))

    report: dict[str, Any] = {
        "mode": "p9-3-renderer-layout-hardening",
        "phase": "P9 Product Release Hardening",
        "checkpoint": P9_3_CHECKPOINT,
        "schema_version": P9_3_SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "p9_2_accept_commit": P9_2_ACCEPT_COMMIT,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "case_probe_count": len(probes),
        "case_probes": [probe.as_dict() for probe in probes],
        "p9_3_renderer_layout_hardening_supported": not errors,
        "arbitrary_current_target_labels_removed": not errors and all(probe.banned_labels_removed for probe in probes),
        "generic_review_placeholder_removed": not errors and all(probe.banned_labels_removed for probe in probes),
        "decision_matrix_renderer_blocks_supported": not errors,
        "title_slide_layout_preserved_supported": not errors,
        "renderer_quality_digest": file_digest(repo_root / "backend/app/services/k_phase/renderer_quality.py") if (repo_root / "backend/app/services/k_phase/renderer_quality.py").exists() else None,
        "next_recommended_step": "Commit P9-3 after targeted runner PASS, then run full runner and Docker smoke.",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifacts_dir / "p9-3-renderer-layout-hardening.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["artifact_outputs"] = {"report": str(report_path)}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-3 renderer/layout hardening checker.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-3 renderer/layout hardening: {report['status']}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
