#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-5a"
SCHEMA_VERSION = "p10.5a.gigachat_api_golden_benchmark.v1"
EXPECTED_BASE_AFTER_P10_4 = "0e29e74b3f275d9c3fbfbd517ff212bf62c88c56"
PUBLIC_API_ENDPOINT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
PUBLIC_API_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_5A_GIGACHAT_API_GOLDEN_BENCHMARK.md",
    "docs/codex/RC3_LOCAL_GIGACHAT_GOLDEN_BENCHMARK_COMPARISON.md",
    "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_rc3_local_gigachat_benchmark_comparison.py",
    "scripts/kw_p10_5a_gigachat_api_golden_benchmark.py",
    "backend/tests/smoke/test_p10_5a_gigachat_api_golden_benchmark.py",
)
SECRET_ENV_NAMES = (
    "KW_RC3_GIGACHAT_AUTHORIZATION_KEY",
    "KW_RC3_GIGACHAT_AUTH_KEY",
    "GIGACHAT_CREDENTIALS",
    "KW_RC3_GIGACHAT_CLIENT_ID",
    "KW_RC3_GIGACHAT_CLIENT_SECRET",
    "KW_RC3_GIGACHAT_ACCESS_TOKEN",
    "KW_RC3_GIGACHAT_BEARER",
    "GIGACHAT_ACCESS_TOKEN",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def git_commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-5a required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_4:
            ancestry = git_commit_is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_4, head)
            if ancestry is False:
                errors.append(f"expected P10-4 baseline {EXPECTED_BASE_AFTER_P10_4} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-4 ancestry for {EXPECTED_BASE_AFTER_P10_4}..{head}")
    return errors


def configured_credential_inputs() -> tuple[str, ...]:
    return tuple(name for name in SECRET_ENV_NAMES if os.environ.get(name, "").strip())


def _safe_env_for_rc3() -> dict[str, str]:
    env = os.environ.copy()
    env["KW_RC3_GIGACHAT_ROUTE"] = "public_api_dev"
    env.setdefault("KW_RC3_GIGACHAT_ENDPOINT", PUBLIC_API_ENDPOINT)
    env.setdefault("KW_RC3_GIGACHAT_AUTH_URL", PUBLIC_API_AUTH_URL)
    env.setdefault("KW_RC3_GIGACHAT_MODEL", "GigaChat")
    env.setdefault("KW_RC3_GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    env["KW_RC3_REQUIRE_LOCAL_GIGACHAT"] = "1"
    env.setdefault("KW_RC3_GIGACHAT_TIMEOUT_SECONDS", "120")
    return env


def run_rc3_public_api(repo_root: Path, artifacts_root: Path) -> tuple[dict[str, Any] | None, str, str, int]:
    report_out = artifacts_root / "p10_5a_rc3_public_api_gigachat_comparison.json"
    command = (
        sys.executable,
        "scripts/kw_rc3_local_gigachat_benchmark_comparison.py",
        "--repo-root",
        str(repo_root),
        "--artifacts-dir",
        str(artifacts_root),
        "--report-out",
        str(report_out),
        "--require-ready",
        "--require-local-gigachat",
        "--json",
    )
    result = subprocess.run(command, cwd=repo_root, env=_safe_env_for_rc3(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = None
    return payload, result.stdout, result.stderr, result.returncode


def validate_rc3_public_api_report(report: dict[str, Any] | None, returncode: int, stdout: str, stderr: str) -> list[str]:
    errors: list[str] = []
    if returncode != 0:
        errors.append(f"RC3 GigaChat API benchmark failed with exit code {returncode}: {stderr.strip() or stdout.strip()[:500]}")
    if report is None:
        errors.append("P10-5a could not parse RC3 JSON report")
        return errors
    expected_cases = len(GOLDEN_CASE_IDS)
    checks = {
        "status": "ready",
        "gigachat_provider_route": "public_api_dev",
        "comparison_status": "compared_local_gigachat_to_fallback",
        "fallback_cases_executed": expected_cases,
        "fallback_cases_ready": expected_cases,
        "local_gigachat_cases_attempted": expected_cases,
        "local_gigachat_cases_used": expected_cases,
        "local_gigachat_cases_ready": expected_cases,
    }
    for key, expected in checks.items():
        if report.get(key) != expected:
            errors.append(f"expected {key}={expected!r}, got {report.get(key)!r}")
    if report.get("public_api_dev_route_used_for_comparison") is not True:
        errors.append("public API dev route was not used for comparison")
    if report.get("public_internet_used_by_rc3_run") is not True:
        errors.append("public internet GigaChat route was not attempted")
    if report.get("production_route_verified") is not False or report.get("offline_intranet_route_verified") is not False:
        errors.append("P10-5a public API benchmark must not claim production/offline intranet route verification")
    if report.get("kimi_level_claimed_by_rc3") is not False or report.get("whole_project_kimi_level_supported") is not False:
        errors.append("RC3/P10-5a must not claim Kimi-level")
    for case in report.get("case_comparisons", []):
        if not isinstance(case, dict):
            continue
        case_id = case.get("case_id")
        if case.get("local_gigachat_attempted") is not True:
            errors.append(f"{case_id}: local_gigachat_attempted is not true")
        if case.get("local_gigachat_used") is not True:
            errors.append(f"{case_id}: local_gigachat_used is not true")
        reason = str(case.get("local_gigachat_fallback_reason_code") or "")
        if reason and reason.lower() not in {"none", "not_applicable", ""}:
            errors.append(f"{case_id}: unexpected GigaChat fallback reason {reason}")
        if case.get("status") not in {"passed", "compared_local_gigachat_to_fallback"}:
            errors.append(f"{case_id}: case comparison did not pass: {case.get("errors")}")
    return errors


def artifact_summary(artifacts_root: Path) -> dict[str, Any]:
    pptx_files = sorted(artifacts_root.rglob("*.pptx"))
    json_files = sorted(artifacts_root.rglob("*.json"))
    return {
        "artifact_root": str(artifacts_root),
        "pptx_file_count": len(pptx_files),
        "json_file_count": len(json_files),
        "pptx_total_size_bytes": sum(path.stat().st_size for path in pptx_files if path.exists()),
        "artifact_file_digest": digest_payload([str(path.relative_to(artifacts_root)) for path in pptx_files + json_files]),
    }


def build_report(repo_root: Path, artifacts_dir: Path | None, require_ready: bool, live: bool, require_gigachat_used: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    credentials = configured_credential_inputs()
    rc3_report: dict[str, Any] | None = None
    live_artifacts: dict[str, Any] = {}
    if live:
        if not credentials:
            errors.append("P10-5a live run requires GigaChat credentials in shell env; do not commit or paste them")
        if artifacts_dir is None:
            artifacts_dir = repo_root / "logs" / "p10_5a_gigachat_api_artifacts"
        if not errors:
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            rc3_report, stdout, stderr, rc3_returncode = run_rc3_public_api(repo_root, artifacts_dir)
            errors.extend(validate_rc3_public_api_report(rc3_report, int(rc3_returncode), stdout, stderr))
            live_artifacts = artifact_summary(artifacts_dir)
    elif require_gigachat_used:
        errors.append("--require-gigachat-used requires --live")
    ready = not errors
    return {
        "mode": "p10-5a-gigachat-api-golden-benchmark",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_4": EXPECTED_BASE_AFTER_P10_4,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "live_gigachat_api_run_performed_by_p10_5a": bool(live),
        "gigachat_provider_route": "public_api_dev",
        "public_api_dev_route_required_by_p10_5a": True,
        "public_internet_used_by_live_p10_5a": bool(live and ready),
        "credential_inputs_configured_count": len(credentials),
        "credential_input_names_configured": credentials,
        "credential_values_recorded": False,
        "rc3_report_status": rc3_report.get("status") if isinstance(rc3_report, dict) else None,
        "rc3_comparison_status": rc3_report.get("comparison_status") if isinstance(rc3_report, dict) else None,
        "fallback_cases_executed": rc3_report.get("fallback_cases_executed") if isinstance(rc3_report, dict) else 0,
        "local_gigachat_cases_used": rc3_report.get("local_gigachat_cases_used") if isinstance(rc3_report, dict) else 0,
        "expected_golden_case_count": len(GOLDEN_CASE_IDS),
        "strict_gigachat_used_for_all_cases": isinstance(rc3_report, dict) and rc3_report.get("local_gigachat_cases_used") == len(GOLDEN_CASE_IDS),
        "production_route_verified_by_p10_5a": False,
        "offline_intranet_route_verified_by_p10_5a": False,
        "public_api_dev_route_is_not_production_evidence": True,
        "human_re_review_required_after_p10_5a": True,
        "approval_state_changed_by_p10_5a": False,
        "golden_decks_auto_approved_by_p10_5a": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_5a": False,
        "api_endpoint_added_by_p10_5a": False,
        "db_schema_migration_added_by_p10_5a": False,
        "frontend_runtime_changed_by_p10_5a": False,
        "dependency_versions_changed_by_p10_5a": False,
        "dockerfiles_changed_by_p10_5a": False,
        "cloud_llm_added_by_p10_5a": False,
        "cloud_vision_added_by_p10_5a": False,
        "kimi_level_claimed_by_p10_5a": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_live_p10_5a": bool(live),
        "live_artifact_summary": live_artifacts,
        "next_recommended_step": "P10-5 - release decision dossier after human re-review; do not change approval state from this automated GigaChat benchmark alone.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio P10-5a strict GigaChat API golden benchmark wrapper.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--live", action="store_true", help="Run the real public GigaChat API benchmark using shell env credentials.")
    parser.add_argument("--require-gigachat-used", action="store_true", help="Fail unless all five golden cases actually use GigaChat output.")
    args = parser.parse_args()
    report = build_report(args.repo_root.resolve(), args.artifacts_dir, args.require_ready, args.live, args.require_gigachat_used)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-5a GigaChat API golden benchmark: {report[status]}")
        print(f"live run: {report[live_gigachat_api_run_performed_by_p10_5a]}")
        print(f"GigaChat cases used: {report[local_gigachat_cases_used]}/{report[expected_golden_case_count]}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
