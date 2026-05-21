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

P9_2_CHECKPOINT = "P9-2"
P9_2_SCHEMA_VERSION = "p9.2.renderer_content_hardening.v1"
P9_BRANCH = "9_Product_Release_Hardening"
P9_1B_BASELINE_COMMIT = "3b39cce346a65809c7bd73cf982a73e7a347e0bb"
GOLDEN_CASES_PATH = "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json"
HUMAN_REVIEW_RESULTS_PATH = "backend/tests/fixtures/p9/p9_1_human_review_results.json"
REQUIRED_FILES = (
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "backend/app/services/k_phase/renderer_quality.py",
    "backend/app/services/k_phase/end_to_end_workflow.py",
    GOLDEN_CASES_PATH,
    HUMAN_REVIEW_RESULTS_PATH,
    "backend/tests/smoke/test_p9_1_human_review_results.py",
    "scripts/kw_p9_1_human_review_results_check.py",
    "scripts/kw_p9_2_renderer_content_hardening_check.py",
    "backend/tests/smoke/test_p9_2_renderer_content_hardening.py",
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "docs/codex/P9_1_GOLDEN_HUMAN_REVIEW_RESULTS.md",
    "docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md",
    "docs/codex/RCH4_GOLDEN_BENCHMARK_HUMAN_REVIEW_WORKFLOW.md",
)
GENERIC_LABELS = ("K1 Plan", "Key point", "Additional source-grounded planning point")
NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_p9_2": False,
    "db_schema_migration_added_by_p9_2": False,
    "frontend_runtime_changed_by_p9_2": False,
    "dependency_versions_changed_by_p9_2": False,
    "dockerfiles_changed_by_p9_2": False,
    "cloud_llm_added_by_p9_2": False,
    "cloud_vision_added_by_p9_2": False,
    "kimi_level_claimed_by_p9_2": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class CaseProbe:
    case_id: str
    slide_count: int
    source_profile: str
    titles: tuple[str, ...]
    generic_labels_removed: bool
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


def text_has_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def plan_text(plan: Any) -> str:
    parts: list[str] = [str(getattr(plan, "deck_title", ""))]
    for slide in getattr(plan, "slides", ()):  # PresentationPlan slides
        parts.append(str(getattr(slide, "title", "")))
        parts.extend(str(bullet) for bullet in getattr(slide, "bullets", ()))
    return "\n".join(parts)


def title_tuple(plan: Any) -> tuple[str, ...]:
    return tuple(str(getattr(slide, "title", "")) for slide in getattr(plan, "slides", ()))


def no_generic_labels(text: str) -> bool:
    return not text_has_any(text, GENERIC_LABELS)


def build_plan(case: dict[str, Any]) -> tuple[Any, dict[str, object]]:
    from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine

    request = K1PlanningRequest(
        source_text=str(case["source_text"]),
        audience=str(case.get("audience") or "operator_review"),
        deck_goal=str(case.get("deck_goal") or "Create a source-grounded presentation plan."),
        target_slide_count=int(case.get("target_slide_count") or 7),
        source_refs=({"source_id": str(case.get("case_id") or "golden_case"), "title": str(case.get("title") or "Golden case")},),
    )
    result = LocalGigaChatPlanningEngine(None).plan(request)
    return result.plan, result.safe_metadata


def evaluate_cases(repo_root: Path) -> tuple[list[CaseProbe], list[str]]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    errors: list[str] = []
    cases = golden_cases(repo_root)
    probes: list[CaseProbe] = []

    required_case_ids = {
        "k0_exec_memo_to_board_deck",
        "k0_arch_doc_to_architecture_deck",
        "k0_project_log_to_status_deck",
        "k0_comparison_table_to_decision_deck",
        "k0_long_docx_pdf_to_structured_presentation",
    }
    seen_case_ids = {str(case.get("case_id")) for case in cases}
    missing = sorted(required_case_ids - seen_case_ids)
    if missing:
        return probes, [f"missing golden case fixture(s): {missing}"]

    for case_id in sorted(required_case_ids):
        plan, metadata = build_plan(case_by_id(cases, case_id))
        combined = plan_text(plan)
        generic_ok = no_generic_labels(combined)
        if not generic_ok:
            errors.append(f"{case_id}: generic fallback label still appears")
        if metadata.get("generic_fallback_labels_removed") is not True:
            errors.append(f"{case_id}: planner metadata did not confirm generic label removal")
        probes.append(
            CaseProbe(
                case_id=case_id,
                slide_count=len(plan.slides),
                source_profile=str(metadata.get("source_profile") or "unknown"),
                titles=title_tuple(plan),
                generic_labels_removed=generic_ok,
                notes=(f"profile={metadata.get('source_profile')}",),
            )
        )

    comparison_plan, comparison_metadata = build_plan(case_by_id(cases, "k0_comparison_table_to_decision_deck"))
    comparison_text = plan_text(comparison_plan)
    if comparison_metadata.get("source_profile") != "comparison_table":
        errors.append("comparison table case was not detected as comparison_table")
    if comparison_metadata.get("comparison_table_decision_matrix_supported") is not True:
        errors.append("comparison table metadata did not report decision-matrix support")
    for expected in ("Decision matrix", "Recommended default", "Rejected default", "Direct local GigaChat", "LiteLLM", "Cloud LLM"):
        if expected.lower() not in comparison_text.lower():
            errors.append(f"comparison table plan missing expected decision content: {expected}")

    project_plan, project_metadata = build_plan(case_by_id(cases, "k0_project_log_to_status_deck"))
    project_text = plan_text(project_plan)
    if project_metadata.get("source_profile") != "project_log":
        errors.append("project log case was not detected as project_log")
    if project_metadata.get("project_log_late_phase_coverage_supported") is not True:
        errors.append("project log metadata did not report late-phase coverage support")
    for expected in ("K4", "K5", "K6", "closure", "Current risks", "Next action", "RC1"):
        if expected.lower() not in project_text.lower():
            errors.append(f"project log plan missing expected late/source coverage: {expected}")

    long_plan, long_metadata = build_plan(case_by_id(cases, "k0_long_docx_pdf_to_structured_presentation"))
    long_text = plan_text(long_plan)
    late_text = "\n".join(title_tuple(long_plan)[-2:]) + "\n" + "\n".join("; ".join(slide.bullets) for slide in long_plan.slides[-2:])
    if long_metadata.get("source_profile") != "long_structured_source":
        errors.append("long DOCX/PDF case was not detected as long_structured_source")
    if long_metadata.get("long_source_filler_slide_prevention_supported") is not True:
        errors.append("long source metadata did not report filler-slide prevention support")
    if len(long_plan.slides) != 10:
        errors.append(f"long source plan expected 10 slides, got {len(long_plan.slides)}")
    for expected in ("Product goal", "Offline constraint", "LLM topology", "Runtime Foundation", "K-phase", "Benchmark requirements", "Release risks", "RC1"):
        if expected.lower() not in long_text.lower():
            errors.append(f"long source plan missing expected section coverage: {expected}")
    if not text_has_any(late_text, ("Evidence package", "Claim guard", "human review", "PPTX", "manifest")):
        errors.append("long source late slides do not appear source-derived or meaningful")

    review_results = load_json(repo_root, HUMAN_REVIEW_RESULTS_PATH)
    if review_results.get("kimi_level_claimed") is not False or review_results.get("whole_project_kimi_level_supported") is not False:
        errors.append("P9-1 human review evidence must remain conservative")

    return probes, errors


def production_gate_errors(repo_root: Path) -> list[str]:
    gate = repo_root / "scripts/kw_production_readiness_gate.py"
    if not gate.exists():
        return ["missing production readiness gate"]
    text = gate.read_text(encoding="utf-8")
    errors: list[str] = []
    for rel in (
        "docs/codex/P9_2_RENDERER_CONTENT_HARDENING.md",
        "scripts/kw_p9_2_renderer_content_hardening_check.py",
        "backend/tests/smoke/test_p9_2_renderer_content_hardening.py",
    ):
        if rel not in text:
            errors.append(f"production readiness gate does not require P9-2 file: {rel}")
    if "P9-2 Renderer/content hardening" not in text:
        errors.append("production readiness gate does not execute P9-2 checker")
    return errors


def static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P9-2 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    if require_ready and branch not in (P9_BRANCH, "unknown"):
        errors.append(f"expected branch {P9_BRANCH}, got {branch}")
    return errors


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    errors.extend(static_errors(repo_root, require_ready))
    probes: list[CaseProbe] = []
    if not errors:
        probes, runtime_errors = evaluate_cases(repo_root)
        errors.extend(runtime_errors)
    errors.extend(production_gate_errors(repo_root))

    report: dict[str, Any] = {
        "mode": "p9-2-renderer-content-hardening",
        "phase": "P9 Product Release Hardening",
        "checkpoint": P9_2_CHECKPOINT,
        "schema_version": P9_2_SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "p9_1b_baseline_commit": P9_1B_BASELINE_COMMIT,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "case_probe_count": len(probes),
        "case_probes": [probe.as_dict() for probe in probes],
        "generic_fallback_labels_removed": not errors and all(probe.generic_labels_removed for probe in probes),
        "comparison_table_decision_matrix_supported": not errors,
        "project_log_late_phase_coverage_supported": not errors,
        "long_source_filler_slide_prevention_supported": not errors,
        "human_review_findings_addressed_by_p9_2": not errors,
        "local_planner_digest": file_digest(repo_root / "backend/app/services/k_phase/local_gigachat_planner.py") if (repo_root / "backend/app/services/k_phase/local_gigachat_planner.py").exists() else None,
        "next_recommended_step": "Commit P9-2 after targeted runner PASS, then run full runner and Docker smoke.",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifacts_dir / "p9-2-renderer-content-hardening.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["artifact_outputs"] = {"report": str(report_path)}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-2 renderer/content hardening checker.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-2 renderer/content hardening: {report['status']}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
