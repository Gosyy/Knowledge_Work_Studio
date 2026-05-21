from __future__ import annotations

import csv
import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import REQUIRED_HUMAN_REVIEW_DIMENSIONS, S10_SCENARIO_IDS
from backend.app.services.slides_service.s13j_human_review_packet import (
    S13K_SALVAGE_SCENARIO_ID,
    S13K_SCHEMA_VERSION,
)
from backend.app.services.slides_service.selected_benchmark_execution_packet import ALLOWED_REVIEW_DECISIONS

S13L_WORKFLOW_ID = "slides.s13k_completed_review_results_ingest"
S13L_PHASE_ID = "S13l"
S13L_SCHEMA_VERSION = "s13l.completed_s13k_review_results_ingest.v1"
S13L_COMPLETED_REVIEW_STATE = "completed_review"
S13L_EXPECTED_SCENARIO_COUNT = len(S10_SCENARIO_IDS)
S13L_REVIEW_RESULTS_MANIFEST_NAME = "s13k_manual_review_results.json"
S13L_REVIEW_SUMMARY_NAME = "s13k_manual_review_summary.md"
S13L_REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "source_packet",
    "reviewed_at",
    "reviewer_id",
    "reviewer_type",
    "decision_counts",
    "selected_offline_workflow_parity_claim_supported",
    "kimi_level_claimed",
    "server3_local_intranet_route_verified",
    "human_reviewer_signature_required_for_strict_human_review",
    "worksheets",
)
S13L_REQUIRED_WORKSHEET_FIELDS = (
    "worksheet_id",
    "scenario_id",
    "review_state",
    "reviewer_id",
    "reviewed_at",
    "decision",
    "scores",
    "slide_level_findings",
    "visual_defects",
    "citation_findings",
    "follow_up_backlog",
    "claim_safety_acknowledgement",
    "salvage_provenance_acknowledgement",
    "completed_human_review_results_present",
    "human_review_results_fabricated",
    "auto_approval_allowed",
    "selected_offline_workflow_parity_claim_supported_now",
    "kimi_level_claimed",
    "server3_local_intranet_route_verified",
)
S13L_FORBIDDEN_ACTIONS = (
    "call_gigachat",
    "rerun_model_generation",
    "modify_s13j_or_s13k_payloads",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class S13lIngestPolicy:
    scenario_id: str
    completed_review_required: bool = True
    allowed_decisions: tuple[str, ...] = ALLOWED_REVIEW_DECISIONS
    required_score_dimensions: tuple[str, ...] = REQUIRED_HUMAN_REVIEW_DIMENSIONS
    auto_approval_allowed: bool = False
    selected_parity_claim_supported_now: bool = False
    kimi_level_claimed: bool = False
    server3_local_intranet_verified: bool = False
    strict_human_signature_may_be_required_downstream: bool = True
    salvage_ack_required: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_decisions"] = list(self.allowed_decisions)
        payload["required_score_dimensions"] = list(self.required_score_dimensions)
        return payload


def build_s13l_ingest_policies() -> tuple[S13lIngestPolicy, ...]:
    return tuple(
        S13lIngestPolicy(scenario_id=scenario_id, salvage_ack_required=scenario_id == S13K_SALVAGE_SCENARIO_ID)
        for scenario_id in S10_SCENARIO_IDS
    )


S13L_INGEST_POLICIES = build_s13l_ingest_policies()


def digest_bytes(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def digest_json(payload: Any) -> str:
    return digest_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def extract_input(input_path: Path, work_dir: Path, label: str) -> tuple[Path, str, str]:
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        out = work_dir / label
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(out)
        return out, input_path.name, digest_file(input_path)
    if input_path.is_dir():
        return input_path, input_path.name, digest_bytes(str(input_path.resolve()).encode("utf-8"))
    if input_path.is_file() and input_path.suffix.lower() == ".json":
        out = work_dir / label
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, out / input_path.name)
        return out, input_path.name, digest_file(input_path)
    raise RuntimeError(f"{label} input must be a ZIP archive, JSON file, or extracted directory: {input_path}")


def find_review_manifest(root: Path) -> Path | None:
    matches = sorted(root.rglob(S13L_REVIEW_RESULTS_MANIFEST_NAME))
    return matches[0] if matches else None


def find_completed_worksheets(root: Path) -> list[Path]:
    preferred = sorted(root.glob("completed_worksheets/*_worksheet.json"))
    if preferred:
        return preferred
    return sorted(root.rglob("*_worksheet.json"))


def _as_dict(payload: Any) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    return payload if isinstance(payload, list) else []


def parse_reviewed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def load_review_results(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    manifest_path = find_review_manifest(root)
    manifest: dict[str, Any] = {}
    if manifest_path is None:
        errors.append(f"missing {S13L_REVIEW_RESULTS_MANIFEST_NAME}")
    else:
        try:
            manifest = _as_dict(read_json(manifest_path))
            if not manifest:
                errors.append(f"{S13L_REVIEW_RESULTS_MANIFEST_NAME} must be a JSON object")
        except Exception as exc:
            errors.append(f"could not load {S13L_REVIEW_RESULTS_MANIFEST_NAME}: {exc}")
    worksheets: list[dict[str, Any]] = []
    for path in find_completed_worksheets(root):
        try:
            payload = read_json(path)
            if isinstance(payload, dict):
                payload = dict(payload)
                payload["_source_file"] = str(path.relative_to(root))
                worksheets.append(payload)
            else:
                errors.append(f"worksheet is not a JSON object: {path}")
        except Exception as exc:
            errors.append(f"could not load worksheet {path}: {exc}")
    if not worksheets and isinstance(manifest.get("review_worksheets"), list):
        worksheets = [item for item in manifest["review_worksheets"] if isinstance(item, dict)]
    if not worksheets:
        errors.append("no completed S13k worksheets found")
    return manifest, worksheets, errors


def load_s13k_packet_index(root: Path | None) -> tuple[dict[str, Any], list[str]]:
    if root is None:
        return {}, []
    path = root / "packet_index.json"
    if not path.exists():
        matches = sorted(root.rglob("packet_index.json"))
        path = matches[0] if matches else path
    if not path.exists():
        return {}, ["S13k packet input missing packet_index.json"]
    try:
        payload = read_json(path)
    except Exception as exc:
        return {}, [f"could not load S13k packet_index.json: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["S13k packet_index.json must be a JSON object"]
    return payload, []


def validate_top_level_manifest(manifest: dict[str, Any], worksheets: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for field in S13L_REQUIRED_TOP_LEVEL_FIELDS:
        if field not in manifest:
            errors.append(f"review manifest missing field: {field}")
    if manifest.get("selected_offline_workflow_parity_claim_supported") is not False:
        errors.append("review manifest must not claim selected offline workflow parity")
    if manifest.get("kimi_level_claimed") is not False:
        errors.append("review manifest must not claim Kimi-level")
    if manifest.get("server3_local_intranet_route_verified") is not False:
        errors.append("review manifest must not claim Server 3 local_intranet verification")
    counts = manifest.get("decision_counts") if isinstance(manifest.get("decision_counts"), dict) else {}
    actual_counts = decision_counts_for_worksheets(worksheets)
    for decision in ALLOWED_REVIEW_DECISIONS:
        if counts.get(decision) is not None and int(counts.get(decision) or 0) != actual_counts[decision]:
            errors.append(f"review manifest decision_counts.{decision} does not match worksheets")
    if manifest.get("reviewer_type") == "assistant_assisted_manual_review_not_independent_human_signature":
        if manifest.get("human_reviewer_signature_required_for_strict_human_review") is not True:
            errors.append("assistant-assisted review must preserve strict human signature requirement")
    return errors


def validate_s13k_packet_index(packet_index: dict[str, Any]) -> list[str]:
    if not packet_index:
        return []
    errors: list[str] = []
    if packet_index.get("s_phase") != "S13k-export":
        errors.append("source packet must be an S13k-export packet")
    if packet_index.get("review_state") != "pending_human_review":
        errors.append("source S13k packet must be pending_human_review before S13l ingest")
    if int(packet_index.get("scenario_count") or 0) != S13L_EXPECTED_SCENARIO_COUNT:
        errors.append("source S13k packet must contain 12 scenarios")
    if packet_index.get("completed_human_review_results_present") is not False:
        errors.append("source S13k packet must be blank before ingest")
    for field in (
        "auto_approval_allowed",
        "selected_offline_workflow_parity_claim_supported_now",
        "kimi_level_claimed",
        "server3_local_intranet_route_verified",
        "credential_values_recorded",
        "raw_secret_values_recorded",
    ):
        if packet_index.get(field) is not False:
            errors.append(f"source packet {field} must be false")
    if packet_index.get("fallback_text_to_minimal_model_adapter_marker_preserved") is not True:
        errors.append("source packet must preserve fallback_text_to_minimal_model_adapter marker")
    return errors


def packet_entries_by_scenario(packet_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = packet_index.get("scenario_packets") if isinstance(packet_index.get("scenario_packets"), list) else []
    return {str(item.get("scenario_id")): item for item in entries if isinstance(item, dict) and item.get("scenario_id")}


def decision_counts_for_worksheets(worksheets: list[dict[str, Any]]) -> dict[str, int]:
    counts = {decision: 0 for decision in ALLOWED_REVIEW_DECISIONS}
    for worksheet in worksheets:
        decision = str(worksheet.get("decision") or "")
        if decision in counts:
            counts[decision] += 1
    return counts


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def validate_scores(scenario_id: str, scores: Any) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    normalized: dict[str, int] = {}
    if not isinstance(scores, dict):
        return [f"{scenario_id}: scores must be an object"], normalized
    for dimension in REQUIRED_HUMAN_REVIEW_DIMENSIONS:
        value = scores.get(dimension)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > 5:
            errors.append(f"{scenario_id}: score for {dimension} must be an integer from 1 to 5")
        else:
            normalized[dimension] = value
    extra = sorted(set(scores) - set(REQUIRED_HUMAN_REVIEW_DIMENSIONS))
    if extra:
        errors.append(f"{scenario_id}: unexpected score dimensions: {extra}")
    return errors, normalized


def validate_completed_worksheet(
    worksheet: dict[str, Any],
    *,
    packet_entry: dict[str, Any] | None,
) -> tuple[list[str], dict[str, Any]]:
    scenario_id = str(worksheet.get("scenario_id") or "")
    errors: list[str] = []
    for field in S13L_REQUIRED_WORKSHEET_FIELDS:
        if field not in worksheet:
            errors.append(f"{scenario_id or '<missing scenario>'}: worksheet missing field: {field}")
    if scenario_id not in S10_SCENARIO_IDS:
        errors.append(f"unexpected scenario_id in completed worksheet: {scenario_id!r}")
    if worksheet.get("review_state") != S13L_COMPLETED_REVIEW_STATE:
        errors.append(f"{scenario_id}: review_state must be {S13L_COMPLETED_REVIEW_STATE}")
    if not isinstance(worksheet.get("reviewer_id"), str) or not worksheet.get("reviewer_id", "").strip():
        errors.append(f"{scenario_id}: reviewer_id must be non-empty")
    if not parse_reviewed_at(worksheet.get("reviewed_at")):
        errors.append(f"{scenario_id}: reviewed_at must be an ISO-8601 timestamp")
    decision = worksheet.get("decision")
    if decision not in ALLOWED_REVIEW_DECISIONS:
        errors.append(f"{scenario_id}: decision must be one of {ALLOWED_REVIEW_DECISIONS}, got {decision!r}")
    score_errors, normalized_scores = validate_scores(scenario_id, worksheet.get("scores"))
    errors.extend(score_errors)
    for list_field in ("slide_level_findings", "visual_defects", "citation_findings", "follow_up_backlog"):
        if not isinstance(worksheet.get(list_field), list):
            errors.append(f"{scenario_id}: {list_field} must be a list")
    if decision in ("request_rework", "reject") and not _nonempty_list(worksheet.get("follow_up_backlog")):
        errors.append(f"{scenario_id}: follow_up_backlog must be non-empty when decision is {decision}")
    if decision == "approve":
        blocking_scores = [dimension for dimension, value in normalized_scores.items() if value <= 2]
        if blocking_scores:
            errors.append(f"{scenario_id}: approve decision is inconsistent with blocking scores: {blocking_scores}")
        for evidence_field in ("visual_defects", "citation_findings", "slide_level_findings"):
            for item in _as_list(worksheet.get(evidence_field)):
                if isinstance(item, dict) and str(item.get("severity") or "").lower() == "blocker":
                    errors.append(f"{scenario_id}: approve decision is inconsistent with blocker in {evidence_field}")
    for flag in (
        "completed_human_review_results_present",
        "claim_safety_acknowledgement",
        "salvage_provenance_acknowledgement",
    ):
        if worksheet.get(flag) is not True:
            errors.append(f"{scenario_id}: {flag} must be true for completed ingest")
    for flag in (
        "human_review_results_fabricated",
        "auto_approval_allowed",
        "selected_offline_workflow_parity_claim_supported_now",
        "kimi_level_claimed",
        "server3_local_intranet_route_verified",
    ):
        if worksheet.get(flag) is not False:
            errors.append(f"{scenario_id}: {flag} must be false")
    if packet_entry:
        if packet_entry.get("worksheet_id") and packet_entry.get("worksheet_id") != worksheet.get("worksheet_id"):
            errors.append(f"{scenario_id}: worksheet_id does not match source S13k packet")
        if packet_entry.get("canonical_payload_digest") and packet_entry.get("canonical_payload_digest") != worksheet.get("canonical_payload_digest"):
            errors.append(f"{scenario_id}: canonical_payload_digest does not match source S13k packet")
    if scenario_id == S13K_SALVAGE_SCENARIO_ID:
        if worksheet.get("salvage_provenance_required") is not True:
            errors.append("executive memo worksheet must preserve salvage_provenance_required=true")
        if worksheet.get("used_text_to_minimal_model_adapter") is not True:
            errors.append("executive memo worksheet must preserve used_text_to_minimal_model_adapter=true")
        if worksheet.get("salvage_generated_fields_are_not_model_generated") is not True:
            errors.append("executive memo worksheet must mark salvage-generated fields as not model-generated")
        if not worksheet.get("source_s13i_response_digest"):
            errors.append("executive memo worksheet must preserve source_s13i_response_digest")
    return errors, normalized_scores


def validate_review_results(
    manifest: dict[str, Any],
    worksheets: list[dict[str, Any]],
    packet_index: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    errors.extend(validate_top_level_manifest(manifest, worksheets))
    packet_index = packet_index or {}
    errors.extend(validate_s13k_packet_index(packet_index))
    by_scenario: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for worksheet in worksheets:
        scenario_id = str(worksheet.get("scenario_id") or "")
        if scenario_id in by_scenario:
            duplicate_ids.append(scenario_id)
        by_scenario[scenario_id] = worksheet
    if duplicate_ids:
        errors.append(f"duplicate completed worksheets: {sorted(duplicate_ids)}")
    missing = sorted(set(S10_SCENARIO_IDS) - set(by_scenario))
    extra = sorted(set(by_scenario) - set(S10_SCENARIO_IDS))
    if missing:
        errors.append(f"missing completed worksheets for scenarios: {missing}")
    if extra:
        errors.append(f"unexpected completed worksheets for scenarios: {extra}")
    packet_by_id = packet_entries_by_scenario(packet_index)
    scenario_summaries: list[dict[str, Any]] = []
    score_mins: dict[str, int] = {}
    blocking_scenario_ids: list[str] = []
    follow_up_backlog: list[dict[str, Any]] = []
    for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
        worksheet = by_scenario.get(scenario_id)
        if worksheet is None:
            continue
        worksheet_errors, normalized_scores = validate_completed_worksheet(worksheet, packet_entry=packet_by_id.get(scenario_id))
        errors.extend(worksheet_errors)
        decision = str(worksheet.get("decision") or "")
        if decision != "approve":
            blocking_scenario_ids.append(scenario_id)
        if normalized_scores:
            score_mins[scenario_id] = min(normalized_scores.values())
            if min(normalized_scores.values()) <= 2 and scenario_id not in blocking_scenario_ids:
                blocking_scenario_ids.append(scenario_id)
        for item in _as_list(worksheet.get("follow_up_backlog")):
            if isinstance(item, dict):
                follow_up_backlog.append({"scenario_id": scenario_id, **item})
            else:
                follow_up_backlog.append({"scenario_id": scenario_id, "summary": str(item)})
        scenario_summaries.append(
            {
                "index": index,
                "scenario_id": scenario_id,
                "worksheet_id": worksheet.get("worksheet_id"),
                "decision": decision,
                "min_score": score_mins.get(scenario_id),
                "reviewer_id": worksheet.get("reviewer_id"),
                "reviewed_at": worksheet.get("reviewed_at"),
                "decision_reason": worksheet.get("decision_reason"),
                "salvage_method": worksheet.get("salvage_method"),
                "used_text_to_minimal_model_adapter": worksheet.get("used_text_to_minimal_model_adapter") is True,
                "salvage_generated_fields_are_not_model_generated": worksheet.get("salvage_generated_fields_are_not_model_generated") is True,
                "source_file": worksheet.get("_source_file"),
            }
        )
    counts = decision_counts_for_worksheets([by_scenario[sid] for sid in S10_SCENARIO_IDS if sid in by_scenario])
    all_completed = len(by_scenario) == S13L_EXPECTED_SCENARIO_COUNT and sum(counts.values()) == S13L_EXPECTED_SCENARIO_COUNT
    all_approved = all_completed and counts["approve"] == S13L_EXPECTED_SCENARIO_COUNT
    summary = {
        "review_worksheet_count": len(worksheets),
        "expected_review_worksheet_count": S13L_EXPECTED_SCENARIO_COUNT,
        "completed_human_review_decision_count": sum(counts.values()),
        "pending_human_review_decision_count": S13L_EXPECTED_SCENARIO_COUNT - sum(counts.values()),
        "approve_count": counts["approve"],
        "request_rework_count": counts["request_rework"],
        "reject_count": counts["reject"],
        "all_scenarios_reviewed": all_completed,
        "all_scenarios_approved": all_approved,
        "blocking_scenario_ids": sorted(set(blocking_scenario_ids)),
        "scenario_min_scores": score_mins,
        "scenario_results": scenario_summaries,
        "follow_up_backlog_item_count": len(follow_up_backlog),
        "follow_up_backlog": follow_up_backlog,
        "overall_review_decision": "approved_all_scenarios" if all_approved else "request_rework_all_scenarios" if counts["request_rework"] else "review_completed_with_blockers",
        "release_decision_after_s13l": "request_rework" if not all_approved else "ready_for_final_human_decision_dossier",
        "selected_offline_workflow_parity_claim_supported_after_s13l": False,
        "kimi_level_claimed_by_s13l": False,
        "server3_local_intranet_route_verified_by_s13l": False,
        "strict_human_signature_required_for_strict_human_review": bool(
            manifest.get("human_reviewer_signature_required_for_strict_human_review") is True
        ),
        "reviewer_type": manifest.get("reviewer_type"),
        "reviewer_id": manifest.get("reviewer_id"),
        "reviewed_at": manifest.get("reviewed_at"),
        "source_packet": manifest.get("source_packet"),
    }
    return errors, summary


def write_ingest_artifacts(artifacts_dir: Path, report: dict[str, Any], worksheets: list[dict[str, Any]]) -> None:
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    write_json(artifacts_dir / "s13l_completed_review_results_ingest_manifest.json", report)
    write_json(
        artifacts_dir / "scenario_review_decisions.json",
        {
            "schema_version": S13L_SCHEMA_VERSION,
            "s_phase": S13L_PHASE_ID,
            "scenario_results": report.get("scenario_results", []),
            "decision_counts": {
                "approve": report.get("approve_count"),
                "request_rework": report.get("request_rework_count"),
                "reject": report.get("reject_count"),
            },
            "release_decision_after_s13l": report.get("release_decision_after_s13l"),
            "selected_offline_workflow_parity_claim_supported_after_s13l": False,
        },
    )
    write_json(
        artifacts_dir / "follow_up_backlog.json",
        {
            "schema_version": S13L_SCHEMA_VERSION,
            "s_phase": S13L_PHASE_ID,
            "follow_up_backlog_item_count": report.get("follow_up_backlog_item_count", 0),
            "follow_up_backlog": report.get("follow_up_backlog", []),
        },
    )
    completed_dir = artifacts_dir / "completed_worksheets"
    completed_dir.mkdir(parents=True, exist_ok=True)
    for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
        worksheet = next((item for item in worksheets if item.get("scenario_id") == scenario_id), None)
        if worksheet is None:
            continue
        worksheet_copy = {k: v for k, v in worksheet.items() if k != "_source_file"}
        write_json(completed_dir / f"{index:02d}_{scenario_id}_worksheet.json", worksheet_copy)
    csv_path = artifacts_dir / "follow_up_backlog.csv"
    rows = report.get("follow_up_backlog", []) if isinstance(report.get("follow_up_backlog"), list) else []
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=("scenario_id", "priority", "area", "summary"), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            if isinstance(row, dict):
                writer.writerow(row)
    summary_lines = [
        "# S13l completed S13k review results ingest",
        "",
        f"Status: {report.get('status')}",
        f"Overall review decision: {report.get('overall_review_decision')}",
        f"Release decision after S13l: {report.get('release_decision_after_s13l')}",
        "",
        "## Decision counts",
        "",
        f"- approve: {report.get('approve_count')}",
        f"- request_rework: {report.get('request_rework_count')}",
        f"- reject: {report.get('reject_count')}",
        "",
        "## Scope boundaries",
        "",
        "- selected offline workflow parity claim supported after S13l: false",
        "- Kimi-level claimed by S13l: false",
        "- Server 3 local_intranet route verified by S13l: false",
        "- auto approval allowed by S13l: false",
        "",
        "## Important caveat",
        "",
        "If reviewer_type is assistant_assisted_manual_review_not_independent_human_signature, strict human review still requires an explicit independent human signature downstream.",
    ]
    (artifacts_dir / "s13l_completed_review_results_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    (artifacts_dir / "operator_handoff_readme.md").write_text(
        "# S13l operator handoff\n\n"
        "S13l ingests completed S13k review worksheets and summarizes decisions/backlog. It does not call GigaChat, "
        "does not alter canonical payloads, does not auto-approve scenarios, and does not support selected parity, "
        "Kimi-level, or Server 3 local_intranet claims by itself.\n",
        encoding="utf-8",
    )


def build_s13l_ingest_report(
    review_results_input: Path,
    *,
    artifacts_dir: Path | None = None,
    s13k_packet_input: Path | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kw_s13l_ingest_") as tmp:
        tmp_dir = Path(tmp)
        review_root, review_source_name, review_source_digest = extract_input(review_results_input, tmp_dir, "review_results")
        s13k_packet_root: Path | None = None
        s13k_packet_name: str | None = None
        s13k_packet_digest: str | None = None
        if s13k_packet_input is not None:
            s13k_packet_root, s13k_packet_name, s13k_packet_digest = extract_input(s13k_packet_input, tmp_dir, "s13k_packet")
        manifest, worksheets, load_errors = load_review_results(review_root)
        packet_index, packet_errors = load_s13k_packet_index(s13k_packet_root)
        errors = list(load_errors) + list(packet_errors)
        validation_summary: dict[str, Any] = {
            "review_worksheet_count": len(worksheets),
            "expected_review_worksheet_count": S13L_EXPECTED_SCENARIO_COUNT,
            "completed_human_review_decision_count": 0,
            "pending_human_review_decision_count": S13L_EXPECTED_SCENARIO_COUNT,
            "approve_count": 0,
            "request_rework_count": 0,
            "reject_count": 0,
            "all_scenarios_reviewed": False,
            "all_scenarios_approved": False,
            "blocking_scenario_ids": [],
            "scenario_min_scores": {},
            "scenario_results": [],
            "follow_up_backlog_item_count": 0,
            "follow_up_backlog": [],
            "overall_review_decision": "not_ready",
            "release_decision_after_s13l": "not_ready",
            "selected_offline_workflow_parity_claim_supported_after_s13l": False,
            "kimi_level_claimed_by_s13l": False,
            "server3_local_intranet_route_verified_by_s13l": False,
        }
        if not errors:
            validation_errors, validation_summary = validate_review_results(manifest, worksheets, packet_index)
            errors.extend(validation_errors)
        status = "ready" if not errors else "failed"
        report = {
            "schema_version": S13L_SCHEMA_VERSION,
            "workflow_id": S13L_WORKFLOW_ID,
            "s_phase": S13L_PHASE_ID,
            "status": status,
            "errors": errors,
            "review_results_source": review_source_name,
            "review_results_source_digest": review_source_digest,
            "s13k_packet_source": s13k_packet_name,
            "s13k_packet_source_digest": s13k_packet_digest,
            "requires_completed_s13k_review_results_by_s13l": True,
            "requires_prior_s13k_packet_by_s13l": True,
            "calls_gigachat_by_s13l": False,
            "reruns_model_generation_by_s13l": False,
            "modifies_canonical_payloads_by_s13l": False,
            "human_review_results_fabricated_by_s13l": False,
            "auto_approval_allowed_by_s13l": False,
            "approval_state_changed_by_s13l": False,
            "credential_values_recorded": False,
            "raw_secret_values_recorded": False,
            "forbidden_actions": list(S13L_FORBIDDEN_ACTIONS),
            "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
            "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
            **validation_summary,
        }
        report["ingest_report_digest"] = digest_json(report)
        if artifacts_dir is not None:
            write_ingest_artifacts(artifacts_dir, report, worksheets)
        return report


def zip_ingest_artifacts(artifacts_dir: Path, zip_out: Path) -> None:
    zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(artifacts_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(artifacts_dir).as_posix())


def validate_s13l_static_contract() -> list[str]:
    errors: list[str] = []
    if len(S13L_INGEST_POLICIES) != S13L_EXPECTED_SCENARIO_COUNT:
        errors.append("S13l must cover exactly 12 S10 scenarios")
    ids = [policy.scenario_id for policy in S13L_INGEST_POLICIES]
    if ids != list(S10_SCENARIO_IDS):
        errors.append("S13l policy scenario order must match S10_SCENARIO_IDS")
    for policy in S13L_INGEST_POLICIES:
        if not policy.completed_review_required:
            errors.append(f"{policy.scenario_id}: completed review must be required")
        if policy.auto_approval_allowed:
            errors.append(f"{policy.scenario_id}: auto approval must not be allowed")
        if policy.selected_parity_claim_supported_now:
            errors.append(f"{policy.scenario_id}: S13l must not claim selected parity")
        if policy.kimi_level_claimed:
            errors.append(f"{policy.scenario_id}: S13l must not claim Kimi-level")
        if policy.server3_local_intranet_verified:
            errors.append(f"{policy.scenario_id}: S13l must not claim Server 3 verification")
        for decision in ALLOWED_REVIEW_DECISIONS:
            if decision not in policy.allowed_decisions:
                errors.append(f"{policy.scenario_id}: missing allowed decision {decision}")
        for dimension in REQUIRED_HUMAN_REVIEW_DIMENSIONS:
            if dimension not in policy.required_score_dimensions:
                errors.append(f"{policy.scenario_id}: missing review score dimension {dimension}")
        if policy.scenario_id == S13K_SALVAGE_SCENARIO_ID and not policy.salvage_ack_required:
            errors.append("executive memo S13l policy must require salvage acknowledgement")
    return errors


def s13l_review_results_ingest_report() -> dict[str, Any]:
    errors = validate_s13l_static_contract()
    return {
        "schema_version": S13L_SCHEMA_VERSION,
        "workflow_id": S13L_WORKFLOW_ID,
        "s_phase": S13L_PHASE_ID,
        "status": "ready" if not errors else "not_ready",
        "errors": errors,
        "scenario_count": len(S13L_INGEST_POLICIES),
        "scenario_ids": [policy.scenario_id for policy in S13L_INGEST_POLICIES],
        "requires_completed_s13k_review_results_by_s13l": True,
        "requires_prior_s13k_packet_by_s13l": True,
        "ingests_completed_review_results_only": True,
        "calls_gigachat_by_s13l": False,
        "reruns_model_generation_by_s13l": False,
        "modifies_canonical_payloads_by_s13l": False,
        "auto_approval_allowed_by_s13l": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13l": False,
        "kimi_level_claimed_by_s13l": False,
        "server3_local_intranet_route_verified_by_s13l": False,
        "strict_human_signature_preserved_when_review_is_assistant_assisted": True,
        "expected_review_state_after_ingest": S13L_COMPLETED_REVIEW_STATE,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
        "forbidden_actions": list(S13L_FORBIDDEN_ACTIONS),
    }
