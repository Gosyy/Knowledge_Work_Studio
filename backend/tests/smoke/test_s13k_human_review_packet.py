from __future__ import annotations

import json
import zipfile
from pathlib import Path

from backend.app.services.slides_service.canonical_schema_adapter import adapt_minimal_model_payload_to_canonical
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.s13j_human_review_packet import (
    S13K_SALVAGE_SCENARIO_ID,
    build_human_review_packet_from_s13j,
    digest_json,
    s13k_human_review_packet_report,
    zip_packet,
)


def _minimal_payload(scenario_id: str) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "deck_title": f"{scenario_id} deck",
        "storyline": ["context", "analysis", "decision", "actions"],
        "slides": [
            {
                "title": f"Slide {idx}",
                "purpose": f"Purpose {idx}",
                "key_claims": ["claim requires source grounding"],
                "visual_intent": "pptx_table",
                "citation_needs": ["source fragment"],
            }
            for idx in range(1, 6)
        ],
        "risks_or_open_questions": ["review required"],
    }


def _canonical_response(scenario_id: str) -> dict[str, object]:
    canonical = adapt_minimal_model_payload_to_canonical(_minimal_payload(scenario_id), scenario_id)
    if scenario_id == S13K_SALVAGE_SCENARIO_ID:
        provenance = canonical["adapter_provenance"]
        provenance["normalization_actions"] = sorted(
            set(provenance["normalization_actions"] + ["fallback_text_to_minimal_model_adapter", "s13j_mark_salvage_fields_not_model_generated"])
        )
        provenance["s13j_salvage_method"] = "fallback_text_to_minimal_model_adapter"
        provenance["s13j_salvage_actions"] = ["strip_markdown_fences", "fallback_text_to_minimal_model_adapter"]
        provenance["source_s13i_response_digest"] = "sha256:source-response"
        provenance["raw_response_text_digest"] = "sha256:raw-response-text"
        provenance["salvage_generated_fields"] = ["deck_title", "storyline", "slides", "risks_or_open_questions"]
        provenance["salvage_generated_fields_are_not_model_generated"] = True
    response = {
        "schema_version": "s13j.executive_memo_salvage.v1",
        "scenario_id": scenario_id,
        "source": "s13j_deterministic_salvage_from_failed_s13i_response"
        if scenario_id == S13K_SALVAGE_SCENARIO_ID
        else "reused_prior_s13i_canonical_valid_output",
        "canonical_schema_valid": True,
        "canonical_schema_errors": [],
        "canonical_payload_digest": digest_json(canonical),
        "completed_human_review_results_present": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
        "canonical_payload": canonical,
    }
    if scenario_id == S13K_SALVAGE_SCENARIO_ID:
        response.update(
            {
                "source_s13i_file": "s13i_01_executive_memo_to_board_deck_retry_response.json",
                "source_s13i_file_digest": "sha256:source-file",
                "source_s13i_response_digest": "sha256:source-response",
                "raw_response_text_digest": "sha256:raw-response-text",
            }
        )
    return response


def _write_fake_s13j_zip(path: Path, *, valid_count: int = 12) -> None:
    scenario_results = []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            response = _canonical_response(scenario_id)
            zf.writestr(f"s13j_{index:02d}_{scenario_id}_merged_canonical_response.json", json.dumps(response))
            result = {
                "scenario_id": scenario_id,
                "source": response["source"],
                "canonical_schema_valid": True,
                "canonical_payload_digest": response["canonical_payload_digest"],
            }
            if scenario_id == S13K_SALVAGE_SCENARIO_ID:
                result.update(
                    {
                        "salvage_method": "fallback_text_to_minimal_model_adapter",
                        "salvage_actions": ["strip_markdown_fences", "fallback_text_to_minimal_model_adapter"],
                        "used_text_to_minimal_model_adapter": True,
                    }
                )
            scenario_results.append(result)
        manifest = {
            "workflow_id": "slides.executive_memo_deterministic_salvage",
            "s_phase": "S13j-live",
            "status": "ready",
            "provider": "GigaChat",
            "route": "public_api_dev",
            "scenario_count": 12,
            "canonical_schema_valid_scenario_count_after_merge": valid_count,
            "salvage_manifest_present": True,
            "scenario_results": scenario_results,
            "calls_gigachat_by_s13j_live": False,
            "completed_human_review_results_present_by_s13j_live": False,
            "auto_approval_allowed_by_s13j_live": False,
            "selected_offline_workflow_parity_claim_supported_now_by_s13j_live": False,
            "kimi_level_claimed_by_s13j_live": False,
            "server3_local_intranet_route_verified_by_s13j_live": False,
            "public_api_dev_route_is_not_server3_proof": True,
            "credential_values_recorded": False,
            "raw_secret_values_recorded": False,
        }
        zf.writestr("s13j_merged_salvage_manifest.json", json.dumps(manifest))
        zf.writestr("s13j_executive_memo_salvage_manifest.json", json.dumps({"status": "ready"}))


def test_s13k_static_contract_ready() -> None:
    report = s13k_human_review_packet_report()
    assert report["status"] == "ready"
    assert report["requires_prior_s13j_merged_12_of_12_artifacts_by_s13k"] is True
    assert report["completed_human_review_results_present_by_s13k"] is False
    assert report["auto_approval_allowed_by_s13k"] is False
    assert report["selected_offline_workflow_parity_claim_supported_now_by_s13k"] is False
    assert report["server3_local_intranet_route_verified_by_s13k"] is False


def test_s13k_exports_blank_human_review_packet_with_salvage_provenance(tmp_path: Path) -> None:
    source_zip = tmp_path / "s13j.zip"
    packet_dir = tmp_path / "packet"
    _write_fake_s13j_zip(source_zip)

    report = build_human_review_packet_from_s13j(source_zip, packet_dir)

    assert report["status"] == "ready"
    assert report["scenario_review_packet_count"] == 12
    assert report["worksheet_count"] == 12
    assert report["completed_human_review_results_present"] is False
    assert report["auto_approval_allowed"] is False
    assert report["salvage_provenance_preserved"] is True
    assert report["fallback_text_to_minimal_model_adapter_marker_preserved"] is True

    executive_worksheet = json.loads((packet_dir / "worksheets/01_executive_memo_to_board_deck_worksheet.json").read_text())
    assert executive_worksheet["decision"] == ""
    assert executive_worksheet["do_not_auto_fill"] is True
    assert executive_worksheet["salvage_provenance_required"] is True
    assert executive_worksheet["used_text_to_minimal_model_adapter"] is True
    assert executive_worksheet["salvage_generated_fields_are_not_model_generated"] is True
    assert executive_worksheet["source_s13i_response_digest"] == "sha256:source-response"

    provenance = json.loads((packet_dir / "provenance/01_executive_memo_to_board_deck_s13j_provenance.json").read_text())
    assert provenance["salvage_performed_by_s13j"] is True
    assert provenance["used_text_to_minimal_model_adapter"] is True
    assert provenance["source_s13i_response_digest"] == "sha256:source-response"
    assert provenance["completed_human_review_results_present"] is False


def test_s13k_rejects_s13j_input_without_12_canonical_valid_scenarios(tmp_path: Path) -> None:
    source_zip = tmp_path / "s13j-invalid.zip"
    packet_dir = tmp_path / "packet"
    _write_fake_s13j_zip(source_zip, valid_count=11)

    report = build_human_review_packet_from_s13j(source_zip, packet_dir)

    assert report["status"] == "failed"
    assert any("12/12 canonical-valid" in error for error in report["errors"])


def test_s13k_packet_zip_contains_required_components(tmp_path: Path) -> None:
    source_zip = tmp_path / "s13j.zip"
    packet_dir = tmp_path / "packet"
    zip_out = tmp_path / "packet.zip"
    _write_fake_s13j_zip(source_zip)

    report = build_human_review_packet_from_s13j(source_zip, packet_dir)
    zip_packet(packet_dir, zip_out)

    assert report["status"] == "ready"
    with zipfile.ZipFile(zip_out) as zf:
        names = set(zf.namelist())
    assert "packet_index.json" in names
    assert "reviewer_instructions.md" in names
    assert "operator_handoff_readme.md" in names
    assert "review_result_ingest_schema.json" in names
    assert "worksheets/01_executive_memo_to_board_deck_worksheet.json" in names
    assert "provenance/01_executive_memo_to_board_deck_s13j_provenance.json" in names
    assert len([name for name in names if name.startswith("worksheets/") and name.endswith("_worksheet.json")]) == 12
