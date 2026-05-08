#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

CHECKPOINT = "P10-7a"
SCHEMA_VERSION = "p10.7a.human_review_worksheet_import_validator.v1"
EXPECTED_BASE_AFTER_P10_6 = "8c5b08bb11ac847fd5a165782f68081029ef43c5"
GOLDEN_CASE_IDS = (
    "k0_exec_memo_to_board_deck",
    "k0_arch_doc_to_architecture_deck",
    "k0_project_log_to_status_deck",
    "k0_comparison_table_to_decision_deck",
    "k0_long_docx_pdf_to_structured_presentation",
)
ALLOWED_DECISIONS = ("approve", "request_rework", "reject")
REQUIRED_REVIEW_FIELDS = (
    "reviewer_id",
    "reviewed_at",
    "decision",
    "scores",
    "slide_level_findings",
    "follow_up_backlog",
)
REQUIRED_FILES = (
    "docs/codex/P10_POST_P9_GOLDEN_REVIEW_PHASE_PLAN.md",
    "docs/codex/P10_4_POST_P9_HUMAN_RE_REVIEW_CAPTURE.md",
    "docs/codex/P10_5_RELEASE_DECISION_DOSSIER.md",
    "docs/codex/P10_6_HUMAN_REVIEW_PACKET_EXPORT.md",
    "docs/codex/P10_7A_HUMAN_REVIEW_WORKSHEET_IMPORT_VALIDATOR.md",
    "backend/tests/fixtures/p9/p9_1_human_review_results.json",
    "scripts/kw_p10_4_post_p9_human_re_review.py",
    "scripts/kw_p10_5_release_decision_dossier.py",
    "scripts/kw_p10_6_human_review_packet_export.py",
    "scripts/kw_p10_7a_human_review_worksheet_import_validator.py",
    "backend/tests/smoke/test_p10_7a_human_review_worksheet_import_validator.py",
)
FORBIDDEN_TRUE_FLAG_PREFIXES = (
    "kimi_level_claimed",
    "whole_project_kimi_level_supported",
    "approval_state_changed",
    "release_approval_granted",
    "golden_decks_auto_approved",
    "server3_offline_intranet_route_verified",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def digest_payload(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing P10-7a required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_P10_6:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_P10_6, head)
            if ancestry is False:
                errors.append(f"expected P10-6 baseline {EXPECTED_BASE_AFTER_P10_6} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify P10-6 ancestry for {EXPECTED_BASE_AFTER_P10_6}..{head}")
    return errors


def review_dimensions(repo_root: Path) -> tuple[dict[str, Any], ...]:
    payload = load_json(repo_root / "backend/tests/fixtures/p9/p9_1_human_review_results.json")
    dims = payload.get("review_dimensions", []) if isinstance(payload, dict) else []
    return tuple(dim for dim in dims if isinstance(dim, dict) and isinstance(dim.get("dimension_id"), str))


def parse_reviewed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        return False


def forbidden_true_flags_at_any_depth(payload: Any) -> list[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            text_key = str(key)
            if value is True and any(text_key == prefix or text_key.startswith(prefix + "_by_") for prefix in FORBIDDEN_TRUE_FLAG_PREFIXES):
                found.add(text_key)
            found.update(forbidden_true_flags_at_any_depth(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(forbidden_true_flags_at_any_depth(item))
    return sorted(found)


def extract_worksheets_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("review_worksheets"), list):
        return [item for item in payload["review_worksheets"] if isinstance(item, dict)]
    if isinstance(payload.get("worksheets"), list):
        return [item for item in payload["worksheets"] if isinstance(item, dict)]
    if isinstance(payload.get("cases"), list):
        return [item for item in payload["cases"] if isinstance(item, dict)]
    if "case_id" in payload:
        return [payload]
    return []


def load_payload_candidates(path: Path) -> tuple[list[tuple[str, Any]], list[str]]:
    errors: list[str] = []
    candidates: list[tuple[str, Any]] = []
    if not path.exists():
        return [], [f"review results path does not exist: {path}"]
    if path.is_dir():
        for item in sorted(path.rglob("*.json")):
            try:
                candidates.append((str(item), load_json(item)))
            except Exception as exc:  # pragma: no cover - defensive report path
                errors.append(f"could not parse JSON file {item}: {exc}")
        return candidates, errors
    if path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path) as archive:
                for name in sorted(n for n in archive.namelist() if n.endswith(".json")):
                    try:
                        candidates.append((f"{path}!{name}", json.loads(archive.read(name).decode("utf-8"))))
                    except Exception as exc:
                        errors.append(f"could not parse JSON entry {path}!{name}: {exc}")
        except zipfile.BadZipFile as exc:
            errors.append(f"review results ZIP is not readable: {path}: {exc}")
        return candidates, errors
    try:
        return [(str(path), load_json(path))], []
    except Exception as exc:
        return [], [f"could not parse review results JSON {path}: {exc}"]


def choose_payload_with_worksheets(candidates: list[tuple[str, Any]]) -> tuple[str | None, Any | None, list[dict[str, Any]]]:
    best: tuple[str | None, Any | None, list[dict[str, Any]]] = (None, None, [])
    for source, payload in candidates:
        worksheets = extract_worksheets_from_payload(payload)
        if len(worksheets) > len(best[2]):
            best = (source, payload, worksheets)
    return best


def validate_scores(case_id: str, scores: Any, dims: tuple[dict[str, Any], ...]) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    normalized: dict[str, int] = {}
    if not isinstance(scores, dict):
        return [f"{case_id}: scores must be an object"], normalized
    for dim in dims:
        dim_id = str(dim["dimension_id"])
        max_score = int(dim.get("max_score") or 5)
        value = scores.get(dim_id)
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{case_id}: scores.{dim_id} must be an integer")
            continue
        if value < 1 or value > max_score:
            errors.append(f"{case_id}: scores.{dim_id} must be within 1..{max_score}, got {value}")
            continue
        normalized[dim_id] = value
    extra = sorted(str(k) for k in scores if str(k) not in {str(dim["dimension_id"]) for dim in dims})
    if extra:
        errors.append(f"{case_id}: scores contains unknown dimensions: {', '.join(extra)}")
    return errors, normalized


def validate_list_field(case_id: str, field: str, value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{case_id}: {field} must be a list"]
    for index, item in enumerate(value):
        if isinstance(item, str):
            if not item.strip():
                errors.append(f"{case_id}: {field}[{index}] must not be empty")
        elif isinstance(item, dict):
            if not item:
                errors.append(f"{case_id}: {field}[{index}] object must not be empty")
        else:
            errors.append(f"{case_id}: {field}[{index}] must be an object or non-empty string")
    return errors


def validate_worksheets(repo_root: Path, worksheets: list[dict[str, Any]], source_payload: Any | None) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    dims = review_dimensions(repo_root)
    expected_dim_ids = tuple(str(dim["dimension_id"]) for dim in dims)
    by_case: dict[str, dict[str, Any]] = {}
    for worksheet in worksheets:
        case_id = str(worksheet.get("case_id") or "")
        if case_id in by_case:
            errors.append(f"duplicate review worksheet for case_id: {case_id}")
        by_case[case_id] = worksheet
    missing = [case_id for case_id in GOLDEN_CASE_IDS if case_id not in by_case]
    unknown = [case_id for case_id in by_case if case_id not in GOLDEN_CASE_IDS]
    if missing:
        errors.append("missing review worksheets for case_ids: " + ", ".join(missing))
    if unknown:
        errors.append("unknown review worksheet case_ids: " + ", ".join(unknown))
    if source_payload is not None:
        for forbidden_key in forbidden_true_flags_at_any_depth(source_payload):
            errors.append(f"review import payload must not set {forbidden_key}=true")
    completed = 0
    pending = 0
    decision_counts = {decision: 0 for decision in ALLOWED_DECISIONS}
    score_mins: dict[str, int] = {}
    for case_id in GOLDEN_CASE_IDS:
        worksheet = by_case.get(case_id)
        if worksheet is None:
            continue
        for field in REQUIRED_REVIEW_FIELDS:
            if field not in worksheet:
                errors.append(f"{case_id}: missing required field {field}")
        decision = worksheet.get("decision")
        if decision in (None, "", "pending_human_review"):
            pending += 1
            errors.append(f"{case_id}: decision remains pending; P10-7a import validation requires completed human review results")
        elif decision not in ALLOWED_DECISIONS:
            errors.append(f"{case_id}: decision must be one of {ALLOWED_DECISIONS}, got {decision!r}")
        else:
            completed += 1
            decision_counts[str(decision)] += 1
        reviewer_id = worksheet.get("reviewer_id")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip():
            errors.append(f"{case_id}: reviewer_id must be a non-empty string")
        if not parse_reviewed_at(worksheet.get("reviewed_at")):
            errors.append(f"{case_id}: reviewed_at must be a non-empty ISO-8601 timestamp")
        score_errors, normalized_scores = validate_scores(case_id, worksheet.get("scores"), dims)
        errors.extend(score_errors)
        if normalized_scores:
            score_mins[case_id] = min(normalized_scores.values())
        errors.extend(validate_list_field(case_id, "slide_level_findings", worksheet.get("slide_level_findings")))
        errors.extend(validate_list_field(case_id, "follow_up_backlog", worksheet.get("follow_up_backlog")))
        if decision in ("request_rework", "reject") and isinstance(worksheet.get("follow_up_backlog"), list) and not worksheet["follow_up_backlog"]:
            errors.append(f"{case_id}: follow_up_backlog must be non-empty when decision is {decision}")
        if decision == "approve" and normalized_scores:
            blocking_scores = [dim for dim in expected_dim_ids if normalized_scores.get(dim, 0) <= 2]
            if blocking_scores:
                errors.append(f"{case_id}: approve decision is inconsistent with blocking scores in: {', '.join(blocking_scores)}")
    summary = {
        "review_worksheet_count": len(worksheets),
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "completed_human_review_decision_count": completed,
        "pending_human_review_decision_count": pending,
        "approve_count": decision_counts["approve"],
        "request_rework_count": decision_counts["request_rework"],
        "reject_count": decision_counts["reject"],
        "human_re_review_completed": completed == len(GOLDEN_CASE_IDS) and len(worksheets) == len(GOLDEN_CASE_IDS),
        "review_dimension_ids": list(expected_dim_ids),
        "case_min_scores": score_mins,
    }
    return errors, summary


def synthetic_completed_payload(repo_root: Path) -> dict[str, Any]:
    dims = review_dimensions(repo_root)
    scores = {str(dim["dimension_id"]): 4 for dim in dims}
    worksheets = []
    for index, case_id in enumerate(GOLDEN_CASE_IDS, start=1):
        worksheets.append(
            {
                "case_id": case_id,
                "reviewer_id": "p10-7a-self-test-reviewer",
                "reviewed_at": f"2026-05-08T12:0{index}:00+02:00",
                "decision": "approve",
                "scores": dict(scores),
                "slide_level_findings": [],
                "follow_up_backlog": [],
            }
        )
    return {"review_worksheets": worksheets, "kimi_level_claimed": False, "whole_project_kimi_level_supported": False}


def build_report(repo_root: Path, review_results: Path | None, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    review_source: str | None = None
    candidate_count = 0
    worksheets: list[dict[str, Any]] = []
    source_payload: Any | None = None
    import_mode = "static_contract_only"
    if review_results is not None:
        import_mode = "operator_supplied_review_results"
        candidates, load_errors = load_payload_candidates(review_results)
        errors.extend(load_errors)
        candidate_count = len(candidates)
        review_source, source_payload, worksheets = choose_payload_with_worksheets(candidates)
        if not worksheets:
            errors.append("no review worksheets were found in the supplied review results payload")
    elif not errors:
        source_payload = synthetic_completed_payload(repo_root)
        review_source = "synthetic_completed_contract_self_test"
        worksheets = extract_worksheets_from_payload(source_payload)
    validation_summary: dict[str, Any] = {
        "review_worksheet_count": len(worksheets),
        "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
        "completed_human_review_decision_count": 0,
        "pending_human_review_decision_count": len(worksheets),
        "approve_count": 0,
        "request_rework_count": 0,
        "reject_count": 0,
        "human_re_review_completed": False,
        "review_dimension_ids": [],
        "case_min_scores": {},
    }
    synthetic_self_test_summary: dict[str, Any] = {}
    if worksheets and not errors:
        validation_errors, computed_summary = validate_worksheets(repo_root, worksheets, source_payload)
        errors.extend(validation_errors)
        if review_results is None:
            synthetic_self_test_summary = computed_summary
            validation_summary = {
                "review_worksheet_count": 0,
                "expected_review_worksheet_count": len(GOLDEN_CASE_IDS),
                "completed_human_review_decision_count": 0,
                "pending_human_review_decision_count": len(GOLDEN_CASE_IDS),
                "approve_count": 0,
                "request_rework_count": 0,
                "reject_count": 0,
                "human_re_review_completed": False,
                "review_dimension_ids": computed_summary.get("review_dimension_ids", []),
                "case_min_scores": {},
            }
        else:
            validation_summary = computed_summary
    ready = not errors
    report = {
        "mode": "p10-7a-human-review-worksheet-import-validator",
        "phase": "P10 Post-P9 Golden Benchmark Regeneration and Human Re-review",
        "checkpoint": CHECKPOINT,
        "schema_version": SCHEMA_VERSION,
        "branch": run_git(repo_root, "branch", "--show-current") or "unknown",
        "commit": run_git(repo_root, "rev-parse", "HEAD") or "unknown",
        "expected_base_after_p10_6": EXPECTED_BASE_AFTER_P10_6,
        "status": "ready" if ready else "failed",
        "errors": errors,
        "import_mode": import_mode,
        "review_results_source": review_source,
        "review_json_candidate_count": candidate_count,
        "validator_contract_self_tested": review_results is None and ready,
        "synthetic_completed_contract_self_test_passed": bool(review_results is None and ready),
        "synthetic_completed_contract_self_test_summary": synthetic_self_test_summary,
        "review_results_importable_by_p10_7a": bool(review_results is not None and ready),
        "release_decision_remains": "defer_pending_human_re_review",
        "release_approval_granted_by_p10_7a": False,
        "approval_state_changed_by_p10_7a": False,
        "golden_decks_auto_approved_by_p10_7a": False,
        "known_non_blocking_warnings_inherited_from_p9": True,
        "dependency_security_remediation_deferred_to_controlled_track": True,
        "p10_5a_public_api_dev_evidence_is_not_server3_offline_proof": True,
        "server3_offline_intranet_route_verified_by_p10_7a": False,
        "full_runner_acceptance_mode": "pass_with_known_non_blocking_warnings",
        "npm_audit_fix_force_run_by_p10_7a": False,
        "api_endpoint_added_by_p10_7a": False,
        "db_schema_migration_added_by_p10_7a": False,
        "frontend_runtime_changed_by_p10_7a": False,
        "dependency_versions_changed_by_p10_7a": False,
        "dockerfiles_changed_by_p10_7a": False,
        "cloud_llm_added_by_p10_7a": False,
        "cloud_vision_added_by_p10_7a": False,
        "kimi_level_claimed_by_p10_7a": False,
        "whole_project_kimi_level_supported": False,
        "network_required_for_p10_7a": False,
        **validation_summary,
    }
    report["validator_report_digest"] = digest_payload(report)
    if review_results is None:
        report["next_recommended_step"] = "Use this validator against real completed P10 human-review worksheets; do not ingest or approve anything until validation passes on real reviewer input."
    elif ready:
        report["next_recommended_step"] = "P10-7 can ingest these completed validated human-review results in a separate controlled patch."
    else:
        report["next_recommended_step"] = "Fix the supplied human-review worksheets and rerun P10-7a before any P10-7 ingest."
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KW Studio P10-7a human review worksheet import validator.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--review-results", type=Path, default=None, help="Completed review worksheet JSON, directory, or P10-6 ZIP packet to validate.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.repo_root.resolve(), args.review_results.resolve() if args.review_results else None, args.require_ready)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"P10-7a human review worksheet import validator: {report['status']}")
        print(f"mode: {report['import_mode']}")
        print(f"worksheets: {report['review_worksheet_count']}/{report['expected_review_worksheet_count']}")
        print(f"completed decisions: {report['completed_human_review_decision_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())

