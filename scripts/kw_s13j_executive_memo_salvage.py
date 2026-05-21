#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
import zipfile
from hashlib import sha256
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.canonical_schema_adapter import validate_canonical_s13g_payload
from backend.app.services.slides_service.executive_memo_salvage import (
    S13J_SCHEMA_VERSION,
    S13J_WORKFLOW_ID,
    adapt_salvaged_payload_to_canonical,
    extract_response_text_from_s13i_payload,
    json_digest,
    salvage_jsonish_minimal_payload,
    text_digest,
)
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.single_scenario_s13h_retry import S13I_RETRY_SCENARIO_ID


def digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def extract_zip(zip_path: Path, work_dir: Path) -> Path:
    out = work_dir / "input"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out)
    return out


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_s13i_manifest(root: Path) -> Path:
    matches = sorted(root.rglob("s13i_single_scenario_retry_manifest.json"))
    if not matches:
        matches = sorted(root.rglob("s13i-single-scenario-retry-report.json"))
    if not matches:
        raise RuntimeError("S13j requires an S13i single-scenario retry manifest")
    return matches[0]


def find_scenario_file(root: Path, scenario_id: str) -> Path | None:
    patterns = (
        f"*_{scenario_id}_merged_canonical_response.json",
        f"*_{scenario_id}_canonical_adapter_response.json",
        f"*{scenario_id}*.json",
    )
    for pattern in patterns:
        matches = sorted(path for path in root.rglob(pattern) if path.is_file())
        if matches:
            return matches[0]
    return None


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically salvage failed S13i executive memo JSON and merge with 11 prior canonical outputs.")
    parser.add_argument("--s13i-live-input", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, required=True)
    parser.add_argument("--require-all-canonical-valid", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    started = time.time()
    artifacts_dir = args.artifacts_dir.resolve()
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    scenario_results: list[dict[str, Any]] = []
    salvage_manifest: dict[str, Any] | None = None

    with tempfile.TemporaryDirectory(prefix="s13j-s13i-input-") as tmp:
        input_root = extract_zip(args.s13i_live_input.resolve(), Path(tmp)) if args.s13i_live_input.is_file() else args.s13i_live_input.resolve()
        manifest_path = find_s13i_manifest(input_root)
        source_manifest = load_json(manifest_path)
        if source_manifest.get("route") != PUBLIC_API_DEV_ROUTE:
            raise RuntimeError("S13i manifest route must be public_api_dev")
        if source_manifest.get("provider") != REQUIRED_PROVIDER:
            raise RuntimeError("S13i manifest provider must be GigaChat")
        if int(source_manifest.get("reused_canonical_scenario_count") or 0) < 11:
            raise RuntimeError("S13j requires an S13i run that reused 11 canonical-valid outputs")
        if int(source_manifest.get("canonical_schema_valid_scenario_count_after_merge") or 0) < 11:
            raise RuntimeError("S13j requires an S13i run with at least 11 canonical-valid outputs after merge")
        if source_manifest.get("credential_values_recorded") is not False or source_manifest.get("raw_secret_values_recorded") is not False:
            raise RuntimeError("S13i manifest must not record credential values")

        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            out_path = artifacts_dir / f"s13j_{index:02d}_{scenario_id}_merged_canonical_response.json"
            source_file = find_scenario_file(input_root, scenario_id)
            if source_file is None:
                errors.append(f"{scenario_id}: missing S13i scenario response file")
                continue
            source_payload = load_json(source_file)

            if scenario_id != S13I_RETRY_SCENARIO_ID:
                if source_payload.get("canonical_schema_valid") is not True:
                    errors.append(f"{scenario_id}: prior S13i output is not canonical-valid and was not selected for salvage")
                source_payload["s13j_reuse_prior_s13i_canonical_output"] = True
                source_payload["s13j_source_prior_file"] = source_file.name
                source_payload["s13j_source_prior_file_digest"] = digest_file(source_file)
                source_payload["completed_human_review_results_present"] = False
                source_payload["selected_offline_workflow_parity_claim_supported_now"] = False
                source_payload["server3_local_intranet_route_verified"] = False
                source_payload["kimi_level_claimed"] = False
                write_json(out_path, source_payload)
                scenario_results.append(
                    {
                        "scenario_id": scenario_id,
                        "source": "reused_prior_s13i_canonical_valid_output",
                        "canonical_schema_valid": source_payload.get("canonical_schema_valid") is True,
                        "canonical_payload_digest": source_payload.get("canonical_payload_digest"),
                    }
                )
                continue

            response_text = extract_response_text_from_s13i_payload(source_payload)
            source_response = source_payload.get("response") if isinstance(source_payload.get("response"), dict) else source_payload
            source_response_digest = source_payload.get("response_digest") or json_digest(source_response)
            raw_response_text_digest = text_digest(response_text)
            if not response_text.strip():
                errors.append(f"{scenario_id}: S13i scenario response text is empty; cannot salvage")
                continue

            salvage_result = salvage_jsonish_minimal_payload(response_text, scenario_id)
            canonical_payload = None
            validation_errors: list[str] = []
            adapter_error = None
            try:
                canonical_payload = adapt_salvaged_payload_to_canonical(
                    salvage_result.payload,
                    scenario_id,
                    source_response_digest=str(source_response_digest),
                    raw_response_text_digest=raw_response_text_digest,
                    salvage_result=salvage_result,
                )
                validation_errors = validate_canonical_s13g_payload(canonical_payload, scenario_id)
            except Exception as exc:
                adapter_error = f"{type(exc).__name__}: {str(exc)[:240]}"
                validation_errors = ["canonical_adapter_failed"]

            canonical_valid = not validation_errors
            retry_payload = {
                "schema_version": S13J_SCHEMA_VERSION,
                "scenario_id": scenario_id,
                "provider": REQUIRED_PROVIDER,
                "route": PUBLIC_API_DEV_ROUTE,
                "source": "s13j_deterministic_salvage_from_failed_s13i_response",
                "s13j_salvage_performed": True,
                "calls_gigachat": False,
                "response_text_present": bool(response_text.strip()),
                "response_text_length": len(response_text),
                "source_s13i_file": source_file.name,
                "source_s13i_file_digest": digest_file(source_file),
                "source_s13i_response_digest": source_response_digest,
                "raw_response_text_digest": raw_response_text_digest,
                "salvage_parse_result": salvage_result.as_dict(),
                "adapter_error": adapter_error,
                "canonical_schema_valid": canonical_valid,
                "canonical_schema_errors": validation_errors,
                "adapter_provenance_present": isinstance(canonical_payload, dict) and isinstance(canonical_payload.get("adapter_provenance"), dict),
                "salvage_generated_fields_are_not_model_generated": bool(
                    isinstance(canonical_payload, dict)
                    and isinstance(canonical_payload.get("adapter_provenance"), dict)
                    and canonical_payload["adapter_provenance"].get("salvage_generated_fields_are_not_model_generated") is True
                ),
                "completed_human_review_results_present": False,
                "auto_approval_allowed": False,
                "selected_offline_workflow_parity_claim_supported_now": False,
                "kimi_level_claimed": False,
                "server3_local_intranet_route_verified": False,
                "raw_secret_values_recorded": False,
                "parsed_or_salvaged_minimal_payload_digest": json_digest(salvage_result.payload),
                "canonical_payload_digest": json_digest(canonical_payload) if canonical_payload is not None else None,
                "parsed_or_salvaged_minimal_payload": salvage_result.payload,
                "canonical_payload": canonical_payload,
            }
            write_json(out_path, retry_payload)
            scenario_results.append(
                {
                    "scenario_id": scenario_id,
                    "source": "s13j_deterministic_salvage_from_failed_s13i_response",
                    "canonical_schema_valid": canonical_valid,
                    "canonical_payload_digest": retry_payload.get("canonical_payload_digest"),
                    "salvage_method": salvage_result.method,
                    "salvage_actions": list(salvage_result.actions),
                    "used_text_to_minimal_model_adapter": salvage_result.used_text_to_minimal_model_adapter,
                    "canonical_schema_errors": validation_errors,
                }
            )
            salvage_manifest = {
                "schema_version": S13J_SCHEMA_VERSION,
                "scenario_id": scenario_id,
                "source_s13i_file": source_file.name,
                "source_s13i_file_digest": digest_file(source_file),
                "source_s13i_response_digest": source_response_digest,
                "raw_response_text_digest": raw_response_text_digest,
                "salvage_result": salvage_result.as_dict(),
                "canonical_schema_valid": canonical_valid,
                "canonical_schema_errors": validation_errors,
                "adapter_error": adapter_error,
                "salvage_generated_fields_are_not_model_generated": retry_payload["salvage_generated_fields_are_not_model_generated"],
                "calls_gigachat": False,
                "completed_human_review_results_present": False,
                "auto_approval_allowed": False,
                "selected_offline_workflow_parity_claim_supported_now": False,
                "kimi_level_claimed": False,
                "server3_local_intranet_route_verified": False,
                "raw_secret_values_recorded": False,
            }
            write_json(artifacts_dir / "s13j_executive_memo_salvage_manifest.json", salvage_manifest)
            if validation_errors:
                errors.append(f"{scenario_id}: deterministic salvage canonical validation failed: {'; '.join(validation_errors[:4])}")

    canonical_valid_count = sum(1 for item in scenario_results if item.get("canonical_schema_valid") is True)
    salvage_valid_count = sum(1 for item in scenario_results if item.get("source") == "s13j_deterministic_salvage_from_failed_s13i_response" and item.get("canonical_schema_valid") is True)
    reused_count = sum(1 for item in scenario_results if item.get("source") == "reused_prior_s13i_canonical_valid_output")

    if args.require_all_canonical_valid and canonical_valid_count != len(S10_SCENARIO_IDS):
        errors.append(f"expected all {len(S10_SCENARIO_IDS)} scenarios canonical-valid after S13j merge, got {canonical_valid_count}")

    manifest = {
        "workflow_id": S13J_WORKFLOW_ID,
        "s_phase": "S13j-live",
        "status": "ready" if not errors else "failed",
        "provider": REQUIRED_PROVIDER,
        "route": PUBLIC_API_DEV_ROUTE,
        "scenario_count": len(S10_SCENARIO_IDS),
        "salvage_scenario_ids": [S13I_RETRY_SCENARIO_ID],
        "salvage_scenario_count": 1,
        "reused_canonical_scenario_count": reused_count,
        "canonical_schema_valid_scenario_count_after_merge": canonical_valid_count,
        "salvaged_canonical_valid_scenario_count": salvage_valid_count,
        "deterministic_salvage_performed_by_s13j_live": salvage_valid_count > 0,
        "calls_gigachat_by_s13j_live": False,
        "credential_values_recorded": False,
        "raw_secret_values_recorded": False,
        "server3_local_intranet_route_verified_by_s13j_live": False,
        "public_api_dev_route_is_not_server3_proof": True,
        "completed_human_review_results_present_by_s13j_live": False,
        "auto_approval_allowed_by_s13j_live": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13j_live": False,
        "kimi_level_claimed_by_s13j_live": False,
        "whole_project_kimi_level_supported": False,
        "artifacts_dir": str(artifacts_dir),
        "salvage_manifest_present": salvage_manifest is not None,
        "scenario_results": scenario_results,
        "elapsed_seconds": round(time.time() - started, 3),
        "errors": errors,
    }
    write_json(artifacts_dir / "s13j_merged_salvage_manifest.json", manifest)

    args.zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.zip_out.resolve(), "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(artifacts_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(artifacts_dir))
    manifest["zip_out"] = str(args.zip_out.resolve())

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13j deterministic executive memo salvage: {manifest['status']}")
        print(f"canonical valid after merge: {canonical_valid_count}/{len(S10_SCENARIO_IDS)}")
        for error in errors:
            print(f"- {error}")
    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
