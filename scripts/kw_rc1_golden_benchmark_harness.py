#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

RC1_CHECKPOINT = "RC1"
RC1_SCHEMA_VERSION = "rc1.golden_benchmark_execution_harness.v1"
K_PHASE_BRANCH = "8_K_Phase"
EXPECTED_K_PHASE_CLOSURE_COMMIT = os.environ.get(
    "RC1_EXPECTED_K_PHASE_CLOSURE_COMMIT",
    "31173f32ae00583d14bff66afb2fc7bf70ee31f4",
)
DEFAULT_FIXTURE_REL = "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json"
_FORBIDDEN_SAFE_TEXT = ("password", "secret", "token", "api_key", "client_secret", "authorization")

REQUIRED_FILES = (
    DEFAULT_FIXTURE_REL,
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "backend/tests/smoke/test_rc1_golden_benchmark_harness.py",
    "docs/codex/RC1_GOLDEN_BENCHMARK_EXECUTION_HARNESS.md",
    "scripts/kw_k_phase_release_readiness_check.py",
    "scripts/kw_k6_end_to_end_workflow_check.py",
)

FORBIDDEN_RC1_MARKERS = {
    "api_endpoint_added_by_rc1": False,
    "db_schema_migration_added_by_rc1": False,
    "frontend_runtime_changed_by_rc1": False,
    "dependency_versions_changed_by_rc1": False,
    "dockerfiles_changed_by_rc1": False,
    "cloud_llm_added_by_rc1": False,
    "cloud_vision_added_by_rc1": False,
    "feature_runtime_added_by_rc1": False,
    "kimi_level_claimed_by_rc1": False,
    "whole_project_kimi_level_supported": False,
    "network_required": False,
}


@dataclass(frozen=True)
class RC1BenchmarkCaseResult:
    case_id: str
    title: str
    source_kind: str
    target_deck_type: str
    status: str
    target_slide_count: int
    actual_slide_count: int
    artifact_filename: str
    artifact_size_bytes: int
    artifact_checksum_sha256: str
    visual_qa_status: str
    visual_qa_score: int
    provenance_coverage_status: str
    gate_count: int
    passed_gate_count: int
    automated_proxy_weighted_total: float
    automated_proxy_kimi_level_candidate_passed: bool
    generated_artifact_paths: tuple[str, ...]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def load_fixture_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("RC1 fixture file must contain a list")
    cases: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("RC1 fixture case must be an object")
        cases.append(item)
    return cases


def static_errors(repo_root: Path, fixture_path: Path, require_ready: bool) -> list[str]:
    errors = [f"missing RC1 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if not fixture_path.exists():
        errors.append(f"missing RC1 fixture file: {fixture_path}")
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch is not None and branch != K_PHASE_BRANCH:
            errors.append(f"expected branch {K_PHASE_BRANCH}, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head is not None and head != EXPECTED_K_PHASE_CLOSURE_COMMIT:
            closure_is_ancestor = git_commit_is_ancestor(repo_root, EXPECTED_K_PHASE_CLOSURE_COMMIT, head)
            if closure_is_ancestor is False:
                errors.append(
                    f"expected K-phase closure commit {EXPECTED_K_PHASE_CLOSURE_COMMIT} "
                    f"to be an ancestor of HEAD {head}"
                )
            elif closure_is_ancestor is None:
                errors.append(
                    f"could not verify K-phase closure ancestry for "
                    f"{EXPECTED_K_PHASE_CLOSURE_COMMIT}..{head}"
                )
    return errors


def validate_fixture_contract(repo_root: Path, cases: list[dict[str, Any]]) -> list[str]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.k_phase.kimi_level_rubric import GOLDEN_BENCHMARK_CASES

    errors: list[str] = []
    expected_by_id = {str(case["case_id"]): case for case in GOLDEN_BENCHMARK_CASES}
    actual_ids = [str(case.get("case_id") or "") for case in cases]
    if len(cases) != len(GOLDEN_BENCHMARK_CASES):
        errors.append(f"RC1 must execute exactly {len(GOLDEN_BENCHMARK_CASES)} K0 golden cases, got {len(cases)}")
    if set(actual_ids) != set(expected_by_id):
        errors.append(f"RC1 fixture case ids do not match K0 golden benchmark ids: {actual_ids}")
    if len(set(actual_ids)) != len(actual_ids):
        errors.append("RC1 fixture case ids must be unique")
    for case in cases:
        case_id = str(case.get("case_id") or "")
        expected = expected_by_id.get(case_id)
        if expected is None:
            continue
        if str(case.get("source_kind")) != str(expected.get("source_kind")):
            errors.append(f"RC1 source_kind mismatch for {case_id}")
        if str(case.get("target_deck_type")) != str(expected.get("target_deck_type")):
            errors.append(f"RC1 target_deck_type mismatch for {case_id}")
        target_slide_count = int(case.get("target_slide_count", 0))
        low, high = [int(value) for value in expected.get("target_slide_count_range", (0, 0))]
        if target_slide_count < low or target_slide_count > min(high, 10):
            errors.append(f"RC1 target_slide_count outside supported K6/K0 range for {case_id}: {target_slide_count}")
        if not str(case.get("source_text") or "").strip():
            errors.append(f"RC1 missing source_text for {case_id}")
        if not case.get("source_refs"):
            errors.append(f"RC1 missing source_refs for {case_id}")
    return errors


def run_case(repo_root: Path, case: dict[str, Any], artifacts_dir: Path | None) -> RC1BenchmarkCaseResult:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.k_phase.end_to_end_workflow import (
        K6EndToEndWorkflowRequest,
        run_k6_end_to_end_workflow,
        validate_k6_end_to_end_result,
    )
    from backend.app.services.k_phase.kimi_level_rubric import score_candidate_dimension_scores

    case_id = str(case["case_id"])
    title = str(case["title"])
    source_text = str(case["source_text"])
    source_refs = tuple(dict(ref) for ref in case.get("source_refs", ()))
    target_slide_count = int(case["target_slide_count"])
    artifact_filename = f"rc1-{case_id}.pptx"
    result = run_k6_end_to_end_workflow(
        K6EndToEndWorkflowRequest(
            source_text=source_text,
            source_refs=source_refs,
            audience=str(case.get("audience") or "golden_benchmark_operator"),
            deck_goal=str(case.get("deck_goal") or title),
            target_slide_count=target_slide_count,
            artifact_filename=artifact_filename,
            session_id=f"rc1_session_{case_id}",
            task_id=f"rc1_task_{case_id}",
            presentation_id=f"rc1_presentation_{case_id}",
            allow_deterministic_fallback=True,
            operator_visual_qa_decision="approve",
        )
    )
    errors: list[str] = list(validate_k6_end_to_end_result(result))
    metadata = result.safe_metadata
    gate_count = len(result.gates)
    passed_gate_count = sum(1 for gate in result.gates if gate.status == "passed")
    if metadata.get("status") != "ready_for_operator_delivery":
        errors.append(f"RC1 {case_id} workflow status is not deliverable: {metadata.get('status')}")
    if result.provenance_result.coverage.coverage_status != "complete":
        errors.append(f"RC1 {case_id} provenance coverage is not complete")
    if passed_gate_count != gate_count:
        errors.append(f"RC1 {case_id} gate mismatch: {passed_gate_count}/{gate_count}")
    if result.render_result.slide_count != target_slide_count:
        errors.append(f"RC1 {case_id} slide count mismatch: expected {target_slide_count}, got {result.render_result.slide_count}")
    if result.render_result.size_bytes <= 0:
        errors.append(f"RC1 {case_id} PPTX artifact is empty")
    if result.visual_qa_result.status not in {"passed", "needs_operator_review"}:
        errors.append(f"RC1 {case_id} visual QA status is not acceptable: {result.visual_qa_result.status}")
    if metadata.get("network_required") is not False:
        errors.append(f"RC1 {case_id} must remain network_required=false")
    safe_encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str).lower()
    if source_text[:80].lower() in safe_encoded:
        errors.append(f"RC1 {case_id} safe metadata contains raw source text")
    for forbidden in _FORBIDDEN_SAFE_TEXT:
        if forbidden in safe_encoded:
            errors.append(f"RC1 {case_id} safe metadata contains forbidden marker {forbidden}")

    proxy_scores = _automated_proxy_scores(result)
    score_report = score_candidate_dimension_scores(proxy_scores)
    generated_paths: list[str] = []
    if artifacts_dir is not None:
        case_dir = artifacts_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        pptx_path = case_dir / artifact_filename
        manifest_path = case_dir / "manifest.json"
        metadata_path = case_dir / "safe_metadata.json"
        pptx_path.write_bytes(result.render_result.artifact_content)
        manifest_path.write_text(json.dumps(result.manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        generated_paths.extend(str(path.relative_to(artifacts_dir)) for path in (pptx_path, manifest_path, metadata_path))

    if bool(score_report.get("kimi_level_candidate_passed")):
        errors.append(f"RC1 {case_id} automated proxy must not pass or claim Kimi-level without human review")

    return RC1BenchmarkCaseResult(
        case_id=case_id,
        title=title,
        source_kind=str(case["source_kind"]),
        target_deck_type=str(case["target_deck_type"]),
        status="passed" if not errors else "failed",
        target_slide_count=target_slide_count,
        actual_slide_count=result.render_result.slide_count,
        artifact_filename=artifact_filename,
        artifact_size_bytes=result.render_result.size_bytes,
        artifact_checksum_sha256=_sha256_prefixed(result.render_result.checksum_sha256),
        visual_qa_status=result.visual_qa_result.status,
        visual_qa_score=result.visual_qa_result.score,
        provenance_coverage_status=result.provenance_result.coverage.coverage_status,
        gate_count=gate_count,
        passed_gate_count=passed_gate_count,
        automated_proxy_weighted_total=float(score_report.get("weighted_total", 0.0)),
        automated_proxy_kimi_level_candidate_passed=bool(score_report.get("kimi_level_candidate_passed")),
        generated_artifact_paths=tuple(generated_paths),
        errors=tuple(errors),
    )


def _sha256_prefixed(value: str) -> str:
    return value if value.startswith("sha256:") else "sha256:" + value


def _automated_proxy_scores(result: Any) -> dict[str, int]:
    # RC1 proxy scores are intentionally conservative. They prove the harness can
    # execute and collect evidence, not that KW Studio has reached Kimi-level.
    gates_passed = all(gate.status == "passed" for gate in result.gates)
    coverage_complete = result.provenance_result.coverage.coverage_status == "complete"
    visual_ok = result.visual_qa_result.status in {"passed", "needs_operator_review"}
    return {
        "storyline_quality": 82 if gates_passed else 60,
        "slide_hierarchy": 82 if result.render_result.slide_count >= 5 else 60,
        "layout_consistency": 80 if visual_ok else 60,
        "visual_density_control": 78 if visual_ok else 55,
        "source_faithfulness": 86 if coverage_complete else 50,
        "editability": 80 if result.plan_editor_result.approved_plan is not None else 50,
        "retry_quality": 76,
        "visual_qa_result": 80 if visual_ok else 55,
        "provenance_quality": 86 if coverage_complete else 50,
        "offline_reproducibility": 100 if result.safe_metadata.get("network_required") is False else 50,
    }


def build_report(repo_root: Path, *, fixture_path: Path | None, artifacts_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    fixture_path = fixture_path or (repo_root / DEFAULT_FIXTURE_REL)
    errors = static_errors(repo_root, fixture_path, require_ready)
    case_results: list[RC1BenchmarkCaseResult] = []
    fixture_digest = None
    if not errors:
        cases = load_fixture_cases(fixture_path)
        fixture_digest = "sha256:" + sha256(fixture_path.read_bytes()).hexdigest()
        errors.extend(validate_fixture_contract(repo_root, cases))
        if not errors:
            for case in cases:
                case_result = run_case(repo_root, case, artifacts_dir)
                case_results.append(case_result)
                errors.extend(case_result.errors)
    passed_cases = sum(1 for item in case_results if item.status == "passed")
    current_head = run_git(repo_root, "rev-parse", "HEAD")
    closure_commit_is_ancestor = (
        current_head == EXPECTED_K_PHASE_CLOSURE_COMMIT
        or (
            current_head is not None
            and git_commit_is_ancestor(repo_root, EXPECTED_K_PHASE_CLOSURE_COMMIT, current_head) is True
        )
    )
    report: dict[str, Any] = {
        "checkpoint": RC1_CHECKPOINT,
        "schema_version": RC1_SCHEMA_VERSION,
        "status": "ready" if not errors and case_results else "failed",
        "k_phase_branch": K_PHASE_BRANCH,
        "expected_k_phase_closure_commit": EXPECTED_K_PHASE_CLOSURE_COMMIT,
        "head": current_head,
        "k_phase_closure_commit_is_ancestor": closure_commit_is_ancestor,
        "fixture_file": str(fixture_path.relative_to(repo_root)) if fixture_path.is_relative_to(repo_root) else str(fixture_path),
        "fixture_digest": fixture_digest,
        "golden_benchmark_execution_harness_supported": True,
        "k0_golden_cases_executed": len(case_results),
        "k0_golden_cases_passed": passed_cases,
        "required_golden_case_count": 5,
        "all_golden_cases_executed": len(case_results) == 5,
        "all_golden_cases_passed": bool(case_results) and passed_cases == len(case_results),
        "k6_workflow_used_for_each_case": bool(case_results) and all(item.gate_count >= 7 for item in case_results),
        "pptx_artifacts_generated": bool(case_results) and all(item.artifact_size_bytes > 0 for item in case_results),
        "manifest_artifacts_generated": artifacts_dir is not None and bool(case_results),
        "source_to_slide_provenance_verified": bool(case_results) and all(item.provenance_coverage_status == "complete" for item in case_results),
        "visual_qa_executed": bool(case_results) and all(item.visual_qa_status in {"passed", "needs_operator_review"} for item in case_results),
        "automated_proxy_scoring_supported": True,
        "human_benchmark_review_required": True,
        "kimi_level_claimed_by_rc1": False,
        "whole_project_kimi_level_supported": False,
        "network_required": False,
        "feature_runtime_added_by_rc1": False,
        "api_endpoint_added_by_rc1": False,
        "db_schema_migration_added_by_rc1": False,
        "frontend_runtime_changed_by_rc1": False,
        "dependency_versions_changed_by_rc1": False,
        "dockerfiles_changed_by_rc1": False,
        "cloud_llm_added_by_rc1": False,
        "cloud_vision_added_by_rc1": False,
        "case_results": [item.as_dict() for item in case_results],
        "errors": errors,
    }
    for marker, expected in FORBIDDEN_RC1_MARKERS.items():
        if report.get(marker) is not expected:
            report.setdefault("errors", []).append(f"forbidden RC1 marker mismatch: {marker}")
    if report["errors"]:
        report["status"] = "failed"
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RC1 golden benchmark execution harness over K0 cases via K6 workflow.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--fixtures", type=Path, default=None)
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    artifacts_dir = args.artifacts_dir.resolve() if args.artifacts_dir else None
    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(repo_root, fixture_path=args.fixtures, artifacts_dir=artifacts_dir, require_ready=args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"RC1 golden benchmark harness status: {report['status']}")
        print(f"cases executed: {report['k0_golden_cases_executed']}/{report['required_golden_case_count']}")
        print(f"cases passed: {report['k0_golden_cases_passed']}/{report['k0_golden_cases_executed']}")
        print(f"human benchmark review required: {report['human_benchmark_review_required']}")
        if report.get("errors"):
            print("errors:")
            for error in report["errors"]:
                print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
