#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

P9_1_CHECKPOINT = "P9-1B"
P9_1_SCHEMA_VERSION = "p9.1b.human_review_results_capture.v1"
P9_BRANCH = "9_Product_Release_Hardening"
SOURCE_BASELINE_BRANCH = "8_K_Phase"
SOURCE_BASELINE_COMMIT = "a2f1aa90fbc56531de85a953447f61a52a63efb7"
RESULTS_PATH = "backend/tests/fixtures/p9/p9_1_human_review_results.json"
EXPECTED_CASE_COUNT = 5
EXPECTED_DIMENSIONS = (
    "storyline_quality",
    "source_faithfulness",
    "visual_hierarchy",
    "density_and_readability",
    "table_chart_decision_quality",
    "provenance_usefulness",
    "visual_qa_result_interpretation",
    "operator_editability",
    "offline_reproducibility",
)
ALLOWED_DECISIONS = {"approve", "request_rework", "reject"}
REQUIRED_FILES = (
    "docs/codex/P9_PRODUCT_RELEASE_HARDENING_PLAN.md",
    "docs/codex/P9_1_GOLDEN_HUMAN_REVIEW_RESULTS.md",
    RESULTS_PATH,
    "scripts/kw_p9_1_human_review_results_check.py",
    "backend/tests/smoke/test_p9_1_human_review_results.py",
    "docs/codex/RCH4_GOLDEN_BENCHMARK_HUMAN_REVIEW_WORKFLOW.md",
    "scripts/kw_rch4_golden_benchmark_human_review.py",
    "docs/codex/KRC_FINAL_BRANCH_CLOSURE.md",
    "scripts/kw_krc_final_branch_closure_check.py",
)
NO_SCOPE_FLAGS = {
    "api_endpoint_added_by_p9_1b": False,
    "db_schema_migration_added_by_p9_1b": False,
    "frontend_runtime_changed_by_p9_1b": False,
    "dependency_versions_changed_by_p9_1b": False,
    "dockerfiles_changed_by_p9_1b": False,
    "cloud_llm_added_by_p9_1b": False,
    "cloud_vision_added_by_p9_1b": False,
    "product_runtime_changed_by_p9_1b": False,
    "kimi_level_claimed_by_p9_1b": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class BacklogItem:
    priority: str
    area: str
    summary: str
    case_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)



def _branch_is_allowed_for_p9(branch: str | None, expected_branch: str) -> bool:
    return branch == expected_branch or branch == "9_Product_Release_Hardening"

def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def git_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def file_digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def load_results(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / RESULTS_PATH).read_text(encoding="utf-8"))


def validate_results(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("checkpoint") != "P9-1":
        errors.append("expected source review checkpoint P9-1")
    if payload.get("schema_version") != "p9.1.golden_benchmark_human_review_results.v1":
        errors.append("unexpected P9-1 review results schema version")
    if payload.get("phase_branch") not in (P9_BRANCH, "9_Product_Release_Hardening"):
        errors.append(f"expected phase_branch {P9_BRANCH}")
    if payload.get("source_baseline_branch") not in (SOURCE_BASELINE_BRANCH, "9_Product_Release_Hardening"):
        errors.append(f"expected source baseline branch {SOURCE_BASELINE_BRANCH}")
    if payload.get("source_baseline_commit") != SOURCE_BASELINE_COMMIT:
        errors.append(f"expected source baseline commit {SOURCE_BASELINE_COMMIT}")
    if payload.get("status") != "completed_human_review":
        errors.append("human review results must be completed")
    if payload.get("human_review_results_completed") is not True:
        errors.append("human_review_results_completed must be true")
    if payload.get("kimi_level_claimed") is not False:
        errors.append("P9-1B must not claim Kimi-level")
    if payload.get("whole_project_kimi_level_supported") is not False:
        errors.append("P9-1B must not claim whole-project Kimi-level")

    cases = payload.get("cases")
    if not isinstance(cases, list):
        return errors + ["cases must be a list"]
    if len(cases) != EXPECTED_CASE_COUNT:
        errors.append(f"expected {EXPECTED_CASE_COUNT} reviewed cases, got {len(cases)}")

    seen: set[str] = set()
    decisions: Counter[str] = Counter()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("case entry must be an object")
            continue
        case_id = str(case.get("case_id") or "")
        if not case_id:
            errors.append("case_id is required")
        if case_id in seen:
            errors.append(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        if case.get("review_status") != "completed":
            errors.append(f"{case_id}: review_status must be completed")
        decision = str(case.get("decision") or "")
        decisions[decision] += 1
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{case_id}: invalid decision {decision}")
        if not str(case.get("decision_reason") or "").strip():
            errors.append(f"{case_id}: decision_reason is required")
        if not str(case.get("reviewer_id") or "").strip():
            errors.append(f"{case_id}: reviewer_id is required")
        if not str(case.get("reviewed_at") or "").strip():
            errors.append(f"{case_id}: reviewed_at is required")
        if case.get("visual_qa_status") not in {"passed", "needs_operator_review"}:
            errors.append(f"{case_id}: visual QA status must be recorded as passed or needs_operator_review")
        if case.get("provenance_coverage_status") != "complete":
            errors.append(f"{case_id}: provenance coverage must be complete in this evidence pack")
        scores = case.get("scores")
        if not isinstance(scores, dict):
            errors.append(f"{case_id}: scores must be an object")
        else:
            missing = sorted(set(EXPECTED_DIMENSIONS) - set(scores))
            if missing:
                errors.append(f"{case_id}: missing score dimensions {missing}")
            for dimension in EXPECTED_DIMENSIONS:
                value = scores.get(dimension)
                if not isinstance(value, int) or value < 1 or value > 5:
                    errors.append(f"{case_id}: invalid score for {dimension}: {value!r}")
        findings = case.get("slide_level_findings")
        if not isinstance(findings, list) or not findings:
            errors.append(f"{case_id}: slide_level_findings must be non-empty")
        backlog = case.get("follow_up_backlog")
        if not isinstance(backlog, list) or not backlog:
            errors.append(f"{case_id}: follow_up_backlog must be non-empty")
        else:
            for item in backlog:
                if not isinstance(item, dict) or not item.get("summary") or not item.get("priority") or not item.get("area"):
                    errors.append(f"{case_id}: follow_up_backlog item must include area, priority, summary")
    summary = payload.get("human_review_summary")
    if not isinstance(summary, dict):
        errors.append("human_review_summary is required")
    else:
        if summary.get("case_count") != EXPECTED_CASE_COUNT:
            errors.append("summary case_count mismatch")
        if summary.get("completed_case_count") != EXPECTED_CASE_COUNT:
            errors.append("summary completed_case_count mismatch")
        if summary.get("kimi_level_claimed") is not False:
            errors.append("summary must not claim Kimi-level")
        if summary.get("whole_project_kimi_level_supported") is not False:
            errors.append("summary must not claim whole-project Kimi-level")
        summary_decisions = summary.get("decision_counts")
        if isinstance(summary_decisions, dict):
            for decision in ALLOWED_DECISIONS:
                if int(summary_decisions.get(decision, 0)) != decisions.get(decision, 0):
                    errors.append(f"summary decision count mismatch for {decision}")
        else:
            errors.append("summary decision_counts is required")
    if decisions.get("request_rework", 0) < 1:
        errors.append("P9-1B should preserve at least one product-quality rework finding")
    return errors


def collect_backlog(payload: dict[str, Any]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], set[str]] = {}
    for case in payload.get("cases", []):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("case_id") or "unknown")
        for item in case.get("follow_up_backlog", []):
            if not isinstance(item, dict):
                continue
            key = (str(item.get("priority") or "P2"), str(item.get("area") or "unknown"), str(item.get("summary") or ""))
            if not key[2]:
                continue
            grouped.setdefault(key, set()).add(case_id)
    backlog = [BacklogItem(priority=priority, area=area, summary=summary, case_ids=tuple(sorted(case_ids))).as_dict() for (priority, area, summary), case_ids in grouped.items()]
    return sorted(backlog, key=lambda item: (str(item["priority"]), str(item["area"]), str(item["summary"])))


def production_gate_errors(repo_root: Path) -> list[str]:
    gate = repo_root / "scripts/kw_production_readiness_gate.py"
    if not gate.exists():
        return ["missing production readiness gate"]
    text = gate.read_text(encoding="utf-8")
    errors: list[str] = []
    for rel in REQUIRED_FILES[:5]:
        if rel not in text:
            errors.append(f"production readiness gate does not require P9-1B file: {rel}")
    if "P9-1B Golden human review results" not in text:
        errors.append("production readiness gate does not execute P9-1B checker")
    return errors


def build_report(repo_root: Path, *, require_ready: bool, artifacts_dir: Path | None = None) -> dict[str, Any]:
    branch = run_git(repo_root, "branch", "--show-current") or "unknown"
    head = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    errors: list[str] = []
    if require_ready and not _branch_is_allowed_for_p9(branch, P9_BRANCH):
        errors.append(f"expected branch {P9_BRANCH}, got {branch}")
    if head != "unknown":
        ancestor = git_is_ancestor(repo_root, SOURCE_BASELINE_COMMIT, head)
        if ancestor is False:
            errors.append(f"source baseline commit {SOURCE_BASELINE_COMMIT} is not an ancestor of HEAD {head}")
        elif ancestor is None and require_ready:
            errors.append(f"could not verify source baseline ancestry for {SOURCE_BASELINE_COMMIT}..{head}")
    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing P9-1B required file: {rel}")

    payload: dict[str, Any] = {}
    if (repo_root / RESULTS_PATH).exists():
        payload = load_results(repo_root)
        errors.extend(validate_results(payload))
    errors.extend(production_gate_errors(repo_root))
    backlog = collect_backlog(payload) if payload else []
    decision_counts = payload.get("human_review_summary", {}).get("decision_counts", {}) if payload else {}
    report: dict[str, Any] = {
        "mode": "p9-1b-human-review-results-capture",
        "phase": "P9 Product Release Hardening",
        "checkpoint": P9_1_CHECKPOINT,
        "schema_version": P9_1_SCHEMA_VERSION,
        "branch": branch,
        "commit": head,
        "source_baseline_branch": SOURCE_BASELINE_BRANCH,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "status": "ready" if not errors else "failed",
        "errors": errors,
        "human_review_results_tracked": bool(payload),
        "human_review_results_completed": payload.get("human_review_results_completed") is True if payload else False,
        "reviewed_case_count": len(payload.get("cases", [])) if payload else 0,
        "decision_counts": decision_counts,
        "request_rework_case_count": int(decision_counts.get("request_rework", 0)) if isinstance(decision_counts, dict) else 0,
        "approve_case_count": int(decision_counts.get("approve", 0)) if isinstance(decision_counts, dict) else 0,
        "reject_case_count": int(decision_counts.get("reject", 0)) if isinstance(decision_counts, dict) else 0,
        "kimi_level_claimed": False,
        "whole_project_kimi_level_supported": False,
        "human_review_backlog_supported": True,
        "follow_up_backlog_item_count": len(backlog),
        "follow_up_backlog": backlog,
        "review_results_digest": file_digest(repo_root / RESULTS_PATH) if (repo_root / RESULTS_PATH).exists() else None,
        "next_recommended_step": "P9-2 — implement the first focused renderer/planning hardening patch from human review findings.",
        **NO_SCOPE_FLAGS,
    }
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        json_path = artifacts_dir / "p9-1b-human-review-results-capture.json"
        backlog_path = artifacts_dir / "p9-1b-follow-up-backlog.json"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        backlog_path.write_text(json.dumps(backlog, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["artifact_outputs"] = {"report": str(json_path), "backlog": str(backlog_path)}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P9-1B human review results capture checker.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), require_ready=args.require_ready, artifacts_dir=args.artifacts_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"P9-1B human review results capture: {report['status']}")
        for error in report["errors"]:
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
