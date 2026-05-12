from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from backend.app.services.slides_service.canonical_schema_adapter import validate_canonical_s13g_payload
from backend.app.services.slides_service.executive_memo_salvage import (
    S13J_EXPECTED_FINAL_CANONICAL_VALID_COUNT,
    executive_memo_salvage_report,
)
from backend.app.services.slides_service.kimi_style_benchmark import (
    ACCEPTED_FINAL_CLAIM_WORDING,
    REQUIRED_AUTOMATED_EVIDENCE,
    REQUIRED_HUMAN_REVIEW_DIMENSIONS,
    S10_SCENARIO_IDS,
)
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.selected_benchmark_execution_packet import (
    ALLOWED_REVIEW_DECISIONS,
    INITIAL_REVIEW_STATE,
    REQUIRED_EVIDENCE_MANIFEST_FIELDS,
    REQUIRED_WORKSHEET_FIELDS,
)

S13K_WORKFLOW_ID = "slides.human_review_packet_from_s13j"
S13K_PHASE_ID = "S13k"
S13K_EXPORT_PHASE_ID = "S13k-export"
S13K_SCHEMA_VERSION = "s13k.human_review_packet_from_s13j.v1"
S13K_SOURCE_MANIFEST_NAME = "s13j_merged_salvage_manifest.json"
S13K_SALVAGE_SCENARIO_ID = "executive_memo_to_board_deck"
S13K_EXPECTED_SCENARIO_COUNT = len(S10_SCENARIO_IDS)
S13K_EXPECTED_CANONICAL_VALID_COUNT = S13J_EXPECTED_FINAL_CANONICAL_VALID_COUNT

S13K_REQUIRED_PACKET_COMPONENTS = (
    "packet_index_json",
    "scenario_evidence_manifest_json",
    "canonical_response_json",
    "human_review_worksheet_json",
    "reviewer_instructions_markdown",
    "operator_handoff_readme_markdown",
    "review_result_ingest_schema_json",
    "s13j_salvage_provenance_json",
    "archive_manifest_json",
)

S13K_REQUIRED_SOURCE_MANIFEST_FIELDS = (
    "status",
    "workflow_id",
    "s_phase",
    "scenario_count",
    "canonical_schema_valid_scenario_count_after_merge",
    "scenario_results",
    "calls_gigachat_by_s13j_live",
    "completed_human_review_results_present_by_s13j_live",
    "auto_approval_allowed_by_s13j_live",
    "selected_offline_workflow_parity_claim_supported_now_by_s13j_live",
    "kimi_level_claimed_by_s13j_live",
    "server3_local_intranet_route_verified_by_s13j_live",
    "public_api_dev_route_is_not_server3_proof",
    "credential_values_recorded",
    "raw_secret_values_recorded",
)

S13K_REQUIRED_PROVENANCE_FIELDS = (
    "scenario_id",
    "source",
    "source_s13j_file",
    "source_s13j_file_digest",
    "source_s13j_packet_digest",
    "source_s13j_manifest_digest",
    "canonical_payload_digest",
    "canonical_schema_valid",
    "review_state",
    "completed_human_review_results_present",
    "auto_approval_allowed",
    "selected_offline_workflow_parity_claim_supported_now",
    "kimi_level_claimed",
    "server3_local_intranet_route_verified",
)

S13K_FORBIDDEN_ACTIONS = (
    "call_gigachat",
    "rerun_model_generation",
    "modify_s13j_canonical_payloads",
    "fabricate_human_review_results",
    "auto_fill_human_review_worksheets",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)


@dataclass(frozen=True)
class S13kHumanReviewPacketPolicy:
    scenario_id: str
    review_state: str = INITIAL_REVIEW_STATE
    human_review_required: bool = True
    worksheet_required: bool = True
    canonical_response_required: bool = True
    provenance_required: bool = True
    salvage_provenance_required: bool = False
    calls_gigachat: bool = False
    completed_human_review_results_present: bool = False
    human_review_results_fabricated: bool = False
    auto_approval_allowed: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False
    credential_values_recorded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_s13k_review_packet_policies() -> tuple[S13kHumanReviewPacketPolicy, ...]:
    return tuple(
        S13kHumanReviewPacketPolicy(
            scenario_id=scenario_id,
            salvage_provenance_required=scenario_id == S13K_SALVAGE_SCENARIO_ID,
        )
        for scenario_id in S10_SCENARIO_IDS
    )


S13K_HUMAN_REVIEW_PACKET_POLICIES = build_s13k_review_packet_policies()


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


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def extract_input(input_path: Path, work_dir: Path) -> tuple[Path, str, str]:
    if input_path.is_file() and input_path.suffix == ".zip":
        out = work_dir / "input"
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(out)
        return out, input_path.name, digest_file(input_path)
    if input_path.is_dir():
        return input_path, input_path.name, digest_bytes(str(input_path.resolve()).encode("utf-8"))
    raise RuntimeError("--s13j-live-input must be a ZIP archive or extracted artifacts directory")


def find_source_manifest(root: Path) -> Path:
    matches = sorted(root.rglob(S13K_SOURCE_MANIFEST_NAME))
    if not matches:
        raise RuntimeError(f"S13k requires {S13K_SOURCE_MANIFEST_NAME} in the S13j ZIP/artifacts")
    return matches[0]


def scenario_response_file(root: Path, scenario_id: str) -> Path | None:
    matches = sorted(root.rglob(f"*_{scenario_id}_merged_canonical_response.json"))
    return matches[0] if matches else None


def canonical_payload_from_response(response_payload: dict[str, Any]) -> dict[str, Any]:
    payload = response_payload.get("canonical_payload")
    if not isinstance(payload, dict):
        raise RuntimeError("merged canonical response must contain canonical_payload object")
    return payload


def _scenario_result_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    results = manifest.get("scenario_results")
    if not isinstance(results, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in results:
        if isinstance(item, dict) and isinstance(item.get("scenario_id"), str):
            out[str(item["scenario_id"])] = item
    return out


def validate_s13j_source_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in S13K_REQUIRED_SOURCE_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"S13j source manifest missing field: {field}")
    if manifest.get("status") != "ready":
        errors.append("S13j source manifest status must be ready")
    if manifest.get("s_phase") != "S13j-live":
        errors.append("S13k requires an S13j-live merged salvage manifest")
    if int(manifest.get("scenario_count") or 0) != S13K_EXPECTED_SCENARIO_COUNT:
        errors.append("S13j source manifest must cover 12 scenarios")
    if int(manifest.get("canonical_schema_valid_scenario_count_after_merge") or 0) != S13K_EXPECTED_CANONICAL_VALID_COUNT:
        errors.append("S13j source manifest must have 12/12 canonical-valid scenarios after merge")
    if manifest.get("salvage_manifest_present") is not True:
        errors.append("S13j source manifest must include salvage_manifest_present=true")
    for field in (
        "calls_gigachat_by_s13j_live",
        "completed_human_review_results_present_by_s13j_live",
        "auto_approval_allowed_by_s13j_live",
        "selected_offline_workflow_parity_claim_supported_now_by_s13j_live",
        "kimi_level_claimed_by_s13j_live",
        "server3_local_intranet_route_verified_by_s13j_live",
        "credential_values_recorded",
        "raw_secret_values_recorded",
    ):
        if manifest.get(field) is not False:
            errors.append(f"S13j source manifest {field} must be false")
    if manifest.get("public_api_dev_route_is_not_server3_proof") is not True:
        errors.append("S13j source manifest must mark public_api_dev as not Server 3 proof")
    results = _scenario_result_by_id(manifest)
    if set(results) != set(S10_SCENARIO_IDS):
        missing = sorted(set(S10_SCENARIO_IDS) - set(results))
        extra = sorted(set(results) - set(S10_SCENARIO_IDS))
        errors.append(f"S13j scenario_results mismatch; missing={missing}, extra={extra}")
    salvage = results.get(S13K_SALVAGE_SCENARIO_ID, {})
    if salvage.get("source") != "s13j_deterministic_salvage_from_failed_s13i_response":
        errors.append("executive memo scenario must be marked as S13j deterministic salvage")
    if salvage.get("used_text_to_minimal_model_adapter") is not True:
        errors.append("S13k requires executive memo worksheet to preserve fallback text-to-minimal-model adapter marker")
    return errors


def build_provenance_record(
    *,
    scenario_id: str,
    source_packet_name: str,
    source_packet_digest: str,
    source_manifest_path: Path,
    source_manifest_digest: str,
    scenario_file: Path,
    scenario_payload: dict[str, Any],
    canonical_payload: dict[str, Any],
    scenario_manifest_entry: dict[str, Any],
) -> dict[str, Any]:
    adapter_provenance = canonical_payload.get("adapter_provenance") if isinstance(canonical_payload.get("adapter_provenance"), dict) else {}
    safety = canonical_payload.get("safety_boundaries") if isinstance(canonical_payload.get("safety_boundaries"), dict) else {}
    source = scenario_manifest_entry.get("source") or scenario_payload.get("source") or "unknown"
    provenance = {
        "schema_version": S13K_SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "source": source,
        "source_s13j_packet": source_packet_name,
        "source_s13j_packet_digest": source_packet_digest,
        "source_s13j_manifest": source_manifest_path.name,
        "source_s13j_manifest_digest": source_manifest_digest,
        "source_s13j_file": scenario_file.name,
        "source_s13j_file_digest": digest_file(scenario_file),
        "canonical_payload_digest": scenario_payload.get("canonical_payload_digest") or scenario_manifest_entry.get("canonical_payload_digest") or digest_json(canonical_payload),
        "canonical_schema_valid": scenario_payload.get("canonical_schema_valid") is True and scenario_manifest_entry.get("canonical_schema_valid") is True,
        "canonical_schema_errors": scenario_payload.get("canonical_schema_errors") or scenario_manifest_entry.get("canonical_schema_errors") or [],
        "review_state": INITIAL_REVIEW_STATE,
        "completed_human_review_results_present": False,
        "human_review_results_fabricated": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
        "public_api_dev_route_is_not_server3_proof": True,
        "credential_values_recorded": False,
        "raw_secret_values_recorded": False,
        "adapter_provenance_present": bool(adapter_provenance),
        "adapter_fields_are_not_model_generated": adapter_provenance.get("adapter_fields_are_not_model_generated") is True,
        "model_provided_fields": adapter_provenance.get("model_provided_fields", []),
        "adapter_added_fields": adapter_provenance.get("adapter_added_fields", []),
        "normalization_actions": adapter_provenance.get("normalization_actions", []),
        "safety_boundaries": {
            "completed_human_review_results_present": safety.get("completed_human_review_results_present"),
            "selected_parity_claim_supported_now": safety.get("selected_parity_claim_supported_now"),
            "kimi_level_claimed": safety.get("kimi_level_claimed"),
            "server3_local_intranet_verified": safety.get("server3_local_intranet_verified"),
            "credential_values_recorded": safety.get("credential_values_recorded"),
        },
        "salvage_provenance_required": scenario_id == S13K_SALVAGE_SCENARIO_ID,
        "salvage_performed_by_s13j": source == "s13j_deterministic_salvage_from_failed_s13i_response",
        "used_text_to_minimal_model_adapter": bool(scenario_manifest_entry.get("used_text_to_minimal_model_adapter")),
        "salvage_method": scenario_manifest_entry.get("salvage_method") or adapter_provenance.get("s13j_salvage_method"),
        "salvage_actions": scenario_manifest_entry.get("salvage_actions") or adapter_provenance.get("s13j_salvage_actions") or [],
        "source_s13i_file": scenario_payload.get("source_s13i_file"),
        "source_s13i_file_digest": scenario_payload.get("source_s13i_file_digest") or scenario_payload.get("s13j_source_prior_file_digest"),
        "source_s13i_response_digest": scenario_payload.get("source_s13i_response_digest") or adapter_provenance.get("source_s13i_response_digest"),
        "raw_response_text_digest": scenario_payload.get("raw_response_text_digest") or adapter_provenance.get("raw_response_text_digest"),
        "salvage_generated_fields": adapter_provenance.get("salvage_generated_fields", []),
        "salvage_generated_fields_are_not_model_generated": adapter_provenance.get("salvage_generated_fields_are_not_model_generated") is True,
        "reviewer_must_verify_salvage_claims": scenario_id == S13K_SALVAGE_SCENARIO_ID,
    }
    return provenance


def validate_provenance_record(provenance: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in S13K_REQUIRED_PROVENANCE_FIELDS:
        if field not in provenance:
            errors.append(f"missing provenance field: {field}")
    for field in (
        "completed_human_review_results_present",
        "human_review_results_fabricated",
        "auto_approval_allowed",
        "selected_offline_workflow_parity_claim_supported_now",
        "kimi_level_claimed",
        "server3_local_intranet_route_verified",
        "credential_values_recorded",
        "raw_secret_values_recorded",
    ):
        if provenance.get(field) is not False:
            errors.append(f"provenance.{field} must be false")
    if provenance.get("review_state") != INITIAL_REVIEW_STATE:
        errors.append("provenance review_state must be pending_human_review")
    if provenance.get("canonical_schema_valid") is not True:
        errors.append("provenance canonical_schema_valid must be true")
    if provenance.get("public_api_dev_route_is_not_server3_proof") is not True:
        errors.append("provenance must mark public_api_dev as not Server 3 proof")
    if provenance.get("adapter_fields_are_not_model_generated") is not True:
        errors.append("provenance must mark adapter fields as not model-generated")
    if provenance.get("scenario_id") == S13K_SALVAGE_SCENARIO_ID:
        if provenance.get("salvage_performed_by_s13j") is not True:
            errors.append("executive memo provenance must mark S13j salvage as performed")
        if provenance.get("used_text_to_minimal_model_adapter") is not True:
            errors.append("executive memo provenance must preserve fallback adapter marker")
        if provenance.get("salvage_generated_fields_are_not_model_generated") is not True:
            errors.append("executive memo provenance must mark salvage-generated fields as not model-generated")
        if not provenance.get("source_s13i_response_digest"):
            errors.append("executive memo provenance must preserve source_s13i_response_digest")
    return errors


def build_worksheet(index: int, scenario_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": S13K_SCHEMA_VERSION,
        "worksheet_id": f"s13k_worksheet_{index:02d}_{scenario_id}",
        "scenario_id": scenario_id,
        "review_state": INITIAL_REVIEW_STATE,
        "reviewer_id": "",
        "reviewed_at": "",
        "decision": "",
        "allowed_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "scores": {dimension: None for dimension in REQUIRED_HUMAN_REVIEW_DIMENSIONS},
        "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
        "slide_level_findings": [],
        "visual_defects": [],
        "citation_findings": [],
        "follow_up_backlog": [],
        "claim_safety_acknowledgement": False,
        "salvage_provenance_acknowledgement": False,
        "salvage_provenance_required": scenario_id == S13K_SALVAGE_SCENARIO_ID,
        "salvage_method": provenance.get("salvage_method"),
        "used_text_to_minimal_model_adapter": provenance.get("used_text_to_minimal_model_adapter"),
        "salvage_generated_fields_are_not_model_generated": provenance.get("salvage_generated_fields_are_not_model_generated"),
        "source_s13i_response_digest": provenance.get("source_s13i_response_digest"),
        "canonical_payload_digest": provenance.get("canonical_payload_digest"),
        "reviewer_must_verify_source_grounding": True,
        "reviewer_must_verify_salvage_claims": scenario_id == S13K_SALVAGE_SCENARIO_ID,
        "do_not_auto_fill": True,
        "completed_human_review_results_present": False,
        "human_review_results_fabricated": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
    }


def build_evidence_manifest(index: int, scenario_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": S13K_SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "source_packet_id": provenance["source_s13j_packet"],
        "approved_plan_snapshot_id": f"s13k_pending_approved_plan_review_{index:02d}_{scenario_id}",
        "generated_pptx_id": f"s13k_pending_generated_pptx_review_{index:02d}_{scenario_id}",
        "artifact_manifest_id": f"s13k_pending_artifact_manifest_review_{index:02d}_{scenario_id}",
        "safe_metadata_id": f"s13k_pending_safe_metadata_review_{index:02d}_{scenario_id}",
        "citation_manifest_id": f"s13k_pending_citation_manifest_review_{index:02d}_{scenario_id}",
        "render_geometry_manifest_id": f"s13k_pending_render_geometry_review_{index:02d}_{scenario_id}",
        "render_based_visual_qa_report_id": f"s13k_pending_render_visual_qa_review_{index:02d}_{scenario_id}",
        "human_review_worksheet_id": f"s13k_worksheet_{index:02d}_{scenario_id}",
        "canonical_response_id": f"{index:02d}_{scenario_id}_canonical_response.json",
        "provenance_id": f"{index:02d}_{scenario_id}_s13j_provenance.json",
        "canonical_payload_digest": provenance["canonical_payload_digest"],
        "canonical_schema_valid": True,
        "required_automated_evidence": list(REQUIRED_AUTOMATED_EVIDENCE),
        "required_evidence_manifest_fields": list(REQUIRED_EVIDENCE_MANIFEST_FIELDS),
        "review_state": INITIAL_REVIEW_STATE,
        "completed_human_review_results_present": False,
        "human_review_results_fabricated": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
        "public_api_dev_route_is_not_server3_proof": True,
        "salvage_provenance_required": scenario_id == S13K_SALVAGE_SCENARIO_ID,
        "salvage_method": provenance.get("salvage_method"),
        "used_text_to_minimal_model_adapter": provenance.get("used_text_to_minimal_model_adapter"),
        "salvage_generated_fields_are_not_model_generated": provenance.get("salvage_generated_fields_are_not_model_generated"),
    }


def build_review_result_ingest_schema() -> dict[str, Any]:
    return {
        "schema_version": S13K_SCHEMA_VERSION,
        "review_state_before_ingest": INITIAL_REVIEW_STATE,
        "allowed_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "required_worksheet_fields": list(REQUIRED_WORKSHEET_FIELDS) + [
            "allowed_decisions",
            "required_human_review_dimensions",
            "salvage_provenance_acknowledgement",
            "do_not_auto_fill",
        ],
        "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
        "auto_approval_allowed": False,
        "fabricated_results_allowed": False,
        "selected_offline_workflow_parity_claim_supported_by_blank_packet": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results": True,
        "accepted_future_claim_wording": ACCEPTED_FINAL_CLAIM_WORDING,
        "reviewer_must_acknowledge_salvage_for_scenarios": [S13K_SALVAGE_SCENARIO_ID],
    }


def copy_scenario_response(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build_human_review_packet_from_s13j(input_path: Path, packet_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="s13k-s13j-input-") as tmp:
        input_root, source_packet_name, source_packet_digest = extract_input(input_path, Path(tmp))
        source_manifest_path = find_source_manifest(input_root)
        source_manifest = read_json(source_manifest_path)
        source_manifest_digest = digest_file(source_manifest_path)
        errors = validate_s13j_source_manifest(source_manifest)
        result_by_id = _scenario_result_by_id(source_manifest)

        if packet_dir.exists():
            shutil.rmtree(packet_dir)
        packet_dir.mkdir(parents=True, exist_ok=True)
        scenarios_dir = packet_dir / "scenarios"
        worksheets_dir = packet_dir / "worksheets"
        provenance_dir = packet_dir / "provenance"
        canonical_dir = packet_dir / "canonical_responses"

        scenario_entries: list[dict[str, Any]] = []
        salvage_provenance_entries: list[dict[str, Any]] = []

        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            scenario_file = scenario_response_file(input_root, scenario_id)
            if scenario_file is None:
                errors.append(f"missing S13j merged canonical response for {scenario_id}")
                continue
            scenario_payload = read_json(scenario_file)
            canonical_payload: dict[str, Any] | None = None
            try:
                canonical_payload = canonical_payload_from_response(scenario_payload)
                canonical_errors = validate_canonical_s13g_payload(canonical_payload, scenario_id)
                if canonical_errors:
                    errors.append(f"{scenario_id}: canonical payload validation failed: {'; '.join(canonical_errors[:4])}")
            except Exception as exc:
                errors.append(f"{scenario_id}: {type(exc).__name__}: {str(exc)[:240]}")
                continue

            provenance = build_provenance_record(
                scenario_id=scenario_id,
                source_packet_name=source_packet_name,
                source_packet_digest=source_packet_digest,
                source_manifest_path=source_manifest_path,
                source_manifest_digest=source_manifest_digest,
                scenario_file=scenario_file,
                scenario_payload=scenario_payload,
                canonical_payload=canonical_payload,
                scenario_manifest_entry=result_by_id.get(scenario_id, {}),
            )
            errors.extend(f"{scenario_id}: {error}" for error in validate_provenance_record(provenance))

            canonical_name = f"{index:02d}_{scenario_id}_canonical_response.json"
            worksheet = build_worksheet(index, scenario_id, provenance)
            evidence = build_evidence_manifest(index, scenario_id, provenance)

            copy_scenario_response(scenario_file, canonical_dir / canonical_name)
            write_json(provenance_dir / f"{index:02d}_{scenario_id}_s13j_provenance.json", provenance)
            write_json(worksheets_dir / f"{index:02d}_{scenario_id}_worksheet.json", worksheet)
            write_json(scenarios_dir / f"{index:02d}_{scenario_id}_evidence_manifest.json", evidence)

            if scenario_id == S13K_SALVAGE_SCENARIO_ID:
                salvage_provenance_entries.append(provenance)

            scenario_entries.append(
                {
                    "scenario_id": scenario_id,
                    "review_state": INITIAL_REVIEW_STATE,
                    "evidence_manifest_id": f"{index:02d}_{scenario_id}_evidence_manifest.json",
                    "worksheet_id": worksheet["worksheet_id"],
                    "worksheet_file": f"worksheets/{index:02d}_{scenario_id}_worksheet.json",
                    "canonical_response_file": f"canonical_responses/{canonical_name}",
                    "provenance_file": f"provenance/{index:02d}_{scenario_id}_s13j_provenance.json",
                    "canonical_payload_digest": provenance["canonical_payload_digest"],
                    "canonical_schema_valid": True,
                    "salvage_provenance_required": scenario_id == S13K_SALVAGE_SCENARIO_ID,
                    "salvage_method": provenance.get("salvage_method"),
                    "used_text_to_minimal_model_adapter": provenance.get("used_text_to_minimal_model_adapter"),
                    "completed_human_review_results_present": False,
                    "auto_approval_allowed": False,
                    "selected_offline_workflow_parity_claim_supported_now": False,
                    "kimi_level_claimed": False,
                    "server3_local_intranet_route_verified": False,
                }
            )

        status = "ready" if not errors and len(scenario_entries) == S13K_EXPECTED_SCENARIO_COUNT else "failed"
        packet_index = {
            "workflow_id": S13K_WORKFLOW_ID,
            "s_phase": S13K_EXPORT_PHASE_ID,
            "schema_version": S13K_SCHEMA_VERSION,
            "status": status,
            "scenario_count": S13K_EXPECTED_SCENARIO_COUNT,
            "scenario_review_packet_count": len(scenario_entries),
            "worksheet_count": len(scenario_entries),
            "canonical_schema_valid_scenario_count_from_s13j": source_manifest.get("canonical_schema_valid_scenario_count_after_merge"),
            "provider": REQUIRED_PROVIDER,
            "route": PUBLIC_API_DEV_ROUTE,
            "source_s13j_packet": source_packet_name,
            "source_s13j_packet_digest": source_packet_digest,
            "source_s13j_manifest": source_manifest_path.name,
            "source_s13j_manifest_digest": source_manifest_digest,
            "review_state": INITIAL_REVIEW_STATE,
            "completed_human_review_results_present": False,
            "human_review_results_fabricated": False,
            "auto_approval_allowed": False,
            "selected_offline_workflow_parity_claim_supported_now": False,
            "selected_offline_workflow_parity_claim_requires_future_completed_results": True,
            "accepted_future_claim_wording": ACCEPTED_FINAL_CLAIM_WORDING,
            "server3_local_intranet_route_verified": False,
            "public_api_dev_route_is_not_server3_proof": True,
            "kimi_level_claimed": False,
            "whole_project_kimi_level_supported": False,
            "credential_values_recorded": False,
            "raw_secret_values_recorded": False,
            "calls_gigachat_by_s13k_export": False,
            "reruns_model_generation_by_s13k_export": False,
            "required_components": list(S13K_REQUIRED_PACKET_COMPONENTS),
            "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
            "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
            "salvage_scenario_ids": [S13K_SALVAGE_SCENARIO_ID],
            "salvage_provenance_preserved": len(salvage_provenance_entries) == 1,
            "salvage_generated_fields_are_not_model_generated": bool(
                salvage_provenance_entries
                and salvage_provenance_entries[0].get("salvage_generated_fields_are_not_model_generated") is True
            ),
            "fallback_text_to_minimal_model_adapter_marker_preserved": bool(
                salvage_provenance_entries
                and salvage_provenance_entries[0].get("used_text_to_minimal_model_adapter") is True
            ),
            "scenario_packets": scenario_entries,
            "errors": errors,
        }

        write_json(packet_dir / "packet_index.json", packet_index)
        write_json(packet_dir / "review_result_ingest_schema.json", build_review_result_ingest_schema())
        write_json(
            packet_dir / "archive_manifest.json",
            {
                "schema_version": S13K_SCHEMA_VERSION,
                "status": status,
                "packet_index": "packet_index.json",
                "source_s13j_packet_digest": source_packet_digest,
                "artifact_file_count": len([path for path in packet_dir.rglob("*") if path.is_file()]) + 1,
                "credential_values_recorded": False,
                "raw_secret_values_recorded": False,
                "completed_human_review_results_present": False,
                "auto_approval_allowed": False,
                "selected_offline_workflow_parity_claim_supported_now": False,
            },
        )
        (packet_dir / "reviewer_instructions.md").write_text(
            "# S13k human review instructions\n\n"
            "Review every worksheet manually. Do not auto-fill decisions, scores, findings, or acknowledgements. "
            "Allowed decisions are approve, request_rework, and reject. No selected offline workflow parity claim is "
            "supported until real completed review results are ingested.\n\n"
            "## Executive memo salvage warning\n\n"
            "The executive_memo_to_board_deck scenario was recovered by S13j deterministic salvage. Its worksheet and "
            "provenance file preserve the fallback_text_to_minimal_model_adapter marker, the source S13i response digest, "
            "and the fact that salvage-generated fields are not model-generated. The reviewer must verify all claims and "
            "source grounding before any decision.\n",
            encoding="utf-8",
        )
        (packet_dir / "operator_handoff_readme.md").write_text(
            "# S13k human review packet handoff\n\n"
            "This packet was exported from the S13j merged 12/12 canonical-valid artifacts. It contains blank human review "
            "worksheets and provenance for each scenario. It does not call GigaChat, does not contain completed human review "
            "results, does not auto-approve scenarios, does not prove Server 3 local_intranet behavior, and does not support "
            "a Kimi-level or selected parity claim by itself.\n",
            encoding="utf-8",
        )
        return packet_index


def zip_packet(packet_dir: Path, zip_out: Path) -> None:
    zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(packet_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(packet_dir))


def validate_s13k_human_review_packet_contract() -> list[str]:
    errors: list[str] = []
    s13j = executive_memo_salvage_report()
    if s13j.get("status") != "ready":
        errors.append("S13k requires S13j deterministic executive memo salvage contract to be ready")
    if s13j.get("expected_final_canonical_valid_count_by_s13j") != S13K_EXPECTED_CANONICAL_VALID_COUNT:
        errors.append("S13k requires S13j expected final canonical-valid count to be 12")
    if len(S13K_HUMAN_REVIEW_PACKET_POLICIES) != S13K_EXPECTED_SCENARIO_COUNT:
        errors.append("S13k must cover 12 selected benchmark scenarios")
    salvage_policies = [policy for policy in S13K_HUMAN_REVIEW_PACKET_POLICIES if policy.salvage_provenance_required]
    if [policy.scenario_id for policy in salvage_policies] != [S13K_SALVAGE_SCENARIO_ID]:
        errors.append("S13k must require salvage provenance only for executive_memo_to_board_deck")
    policy_by_id = {policy.scenario_id: policy for policy in S13K_HUMAN_REVIEW_PACKET_POLICIES}
    for scenario_id in S10_SCENARIO_IDS:
        policy = policy_by_id.get(scenario_id)
        if policy is None:
            errors.append(f"missing S13k policy for {scenario_id}")
            continue
        for name in ("human_review_required", "worksheet_required", "canonical_response_required", "provenance_required"):
            if getattr(policy, name) is not True:
                errors.append(f"{scenario_id}: {name} must be true")
        for name in (
            "calls_gigachat",
            "completed_human_review_results_present",
            "human_review_results_fabricated",
            "auto_approval_allowed",
            "selected_parity_claim_supported_now",
            "server3_local_intranet_verified",
            "kimi_level_claimed",
            "credential_values_recorded",
        ):
            if getattr(policy, name) is not False:
                errors.append(f"{scenario_id}: {name} must be false")
        if policy.review_state != INITIAL_REVIEW_STATE:
            errors.append(f"{scenario_id}: review_state must be pending_human_review")
    return errors


def s13k_human_review_packet_report() -> dict[str, Any]:
    errors = validate_s13k_human_review_packet_contract()
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13K_WORKFLOW_ID,
        "s_phase": S13K_PHASE_ID,
        "s13k_human_review_packet_from_s13j_ready": not errors,
        "scenario_count": len(S13K_HUMAN_REVIEW_PACKET_POLICIES),
        "worksheet_count_required_by_s13k": len(S13K_HUMAN_REVIEW_PACKET_POLICIES),
        "requires_prior_s13j_merged_12_of_12_artifacts_by_s13k": True,
        "expected_canonical_valid_count_from_s13j_by_s13k": S13K_EXPECTED_CANONICAL_VALID_COUNT,
        "required_source_manifest_fields": list(S13K_REQUIRED_SOURCE_MANIFEST_FIELDS),
        "required_packet_components": list(S13K_REQUIRED_PACKET_COMPONENTS),
        "required_provenance_fields": list(S13K_REQUIRED_PROVENANCE_FIELDS),
        "required_human_review_dimensions": list(REQUIRED_HUMAN_REVIEW_DIMENSIONS),
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "review_state_after_s13k_export": INITIAL_REVIEW_STATE,
        "calls_gigachat_by_s13k_static_check": False,
        "reruns_model_generation_by_s13k_static_check": False,
        "completed_human_review_results_present_by_s13k": False,
        "human_review_results_fabricated_by_s13k": False,
        "auto_approval_allowed_by_s13k": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13k": False,
        "selected_offline_workflow_parity_claim_requires_future_completed_results_by_s13k": True,
        "accepted_future_claim_wording_by_s13k": ACCEPTED_FINAL_CLAIM_WORDING,
        "server3_local_intranet_route_verified_by_s13k": False,
        "public_api_dev_route_is_not_server3_proof_by_s13k": True,
        "credential_values_recorded_by_s13k": False,
        "raw_secret_values_recorded_by_s13k": False,
        "kimi_level_claimed_by_s13k": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13k": False,
        "db_schema_migration_added_by_s13k": False,
        "frontend_runtime_changed_by_s13k": False,
        "dependency_versions_changed_by_s13k": False,
        "dockerfiles_changed_by_s13k": False,
        "next_recommended_step": "Run S13k export against the S13j merged 12/12 ZIP, then perform real manual human review; do not claim selected parity until completed review results are ingested.",
        "forbidden_actions": list(S13K_FORBIDDEN_ACTIONS),
        "contract": {"policies": [policy.as_dict() for policy in S13K_HUMAN_REVIEW_PACKET_POLICIES]},
        "errors": errors,
    }
