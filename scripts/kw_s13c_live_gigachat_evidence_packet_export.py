#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path
from typing import Any

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_evidence_packet import (
    EVIDENCE_PACKET_STATE,
    REQUIRED_EVIDENCE_PACKET_COMPONENTS,
    REQUIRED_SCENARIO_EVIDENCE_FIELDS,
)
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.selected_benchmark_execution_packet import INITIAL_REVIEW_STATE


def _digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _safe_json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_zip(zip_path: Path, work_dir: Path) -> Path:
    out = work_dir / "input"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out)
    return out


def _find_manifest(root: Path) -> Path:
    matches = sorted(root.rglob("s13b_live_generation_manifest.json"))
    if not matches:
        raise RuntimeError("S13c export requires s13b_live_generation_manifest.json in the live ZIP/artifacts")
    return matches[0]


def _scenario_response_file(root: Path, scenario_id: str) -> Path | None:
    matches = sorted(root.rglob(f"*_{scenario_id}_gigachat_response.json"))
    return matches[0] if matches else None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def build_packet(input_path: Path, out_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="s13c-live-input-") as tmp:
        tmp_path = Path(tmp)
        if input_path.is_file() and input_path.suffix == ".zip":
            input_root = _extract_zip(input_path, tmp_path)
        elif input_path.is_dir():
            input_root = input_path
        else:
            raise RuntimeError("--s13b-live-input must be a ZIP archive or extracted artifacts directory")

        manifest_path = _find_manifest(input_root)
        manifest = _safe_json_load(manifest_path)
        if manifest.get("status") != "ready":
            raise RuntimeError("S13b live manifest status must be ready")
        if manifest.get("route") != PUBLIC_API_DEV_ROUTE:
            raise RuntimeError("S13b live manifest route must be public_api_dev")
        if int(manifest.get("successful_scenario_generation_count") or 0) != 12:
            raise RuntimeError("S13b live manifest must include 12 successful scenario generations")
        if manifest.get("credential_values_recorded") is not False or manifest.get("raw_secret_values_recorded") is not False:
            raise RuntimeError("S13b live manifest must not record credential values")

        out_dir.mkdir(parents=True, exist_ok=True)
        scenarios_dir = out_dir / "scenarios"
        worksheets_dir = out_dir / "worksheets"
        packet_entries: list[dict[str, Any]] = []
        errors: list[str] = []

        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            response_path = _scenario_response_file(input_root, scenario_id)
            if response_path is None:
                errors.append(f"missing live response JSON for {scenario_id}")
                continue
            response_payload = _safe_json_load(response_path)
            summary = {key: value for key, value in response_payload.items() if key != "response"}
            scenario_packet = {
                "scenario_id": scenario_id,
                "provider": summary.get("provider", REQUIRED_PROVIDER),
                "route": summary.get("route", PUBLIC_API_DEV_ROUTE),
                "model": summary.get("model"),
                "live_generation_manifest_id": manifest_path.name,
                "scenario_model_response_id": response_path.name,
                "model_response_digest": summary.get("response_digest") or _digest_file(response_path),
                "model_response_text_present": bool(summary.get("response_text_present")),
                "response_text_length": int(summary.get("response_text_length") or 0),
                "worksheet_id": f"s13c_worksheet_{index:02d}_{scenario_id}",
                "review_state": INITIAL_REVIEW_STATE,
                "evidence_packet_state": EVIDENCE_PACKET_STATE,
                "credential_values_recorded": False,
                "server3_local_intranet_verified": False,
                "completed_human_review_results_present": False,
                "selected_parity_claim_supported_now": False,
                "required_fields": list(REQUIRED_SCENARIO_EVIDENCE_FIELDS),
            }
            worksheet = {
                "worksheet_id": scenario_packet["worksheet_id"],
                "scenario_id": scenario_id,
                "review_state": INITIAL_REVIEW_STATE,
                "reviewer_id": "",
                "reviewed_at": "",
                "decision": "",
                "scores": {},
                "slide_level_findings": [],
                "visual_defects": [],
                "citation_findings": [],
                "follow_up_backlog": [],
                "claim_safety_acknowledgement": False,
                "do_not_auto_fill": True,
            }
            _write_json(scenarios_dir / f"{index:02d}_{scenario_id}_evidence_packet.json", scenario_packet)
            _write_json(worksheets_dir / f"{index:02d}_{scenario_id}_worksheet.json", worksheet)
            packet_entries.append(scenario_packet)

        status = "ready" if not errors and len(packet_entries) == 12 else "failed"
        packet_index = {
            "workflow_id": "slides.live_gigachat_evidence_packet_export",
            "s_phase": "S13c-export",
            "status": status,
            "scenario_count": len(S10_SCENARIO_IDS),
            "scenario_evidence_packet_count": len(packet_entries),
            "provider": REQUIRED_PROVIDER,
            "route": PUBLIC_API_DEV_ROUTE,
            "source_live_manifest_digest": _digest_file(manifest_path),
            "source_live_manifest": manifest_path.name,
            "review_state": INITIAL_REVIEW_STATE,
            "completed_human_review_results_present": False,
            "human_review_results_fabricated": False,
            "auto_approval_allowed": False,
            "selected_offline_workflow_parity_claim_supported_now": False,
            "server3_local_intranet_route_verified": False,
            "public_api_dev_route_is_not_server3_proof": True,
            "kimi_level_claimed": False,
            "required_components": list(REQUIRED_EVIDENCE_PACKET_COMPONENTS),
            "scenario_packets": packet_entries,
            "errors": errors,
        }
        _write_json(out_dir / "packet_index.json", packet_index)
        (out_dir / "reviewer_instructions.md").write_text(
            "# S13c human review instructions\n\n"
            "Review each scenario worksheet manually. Do not auto-fill decisions. "
            "Allowed decisions: approve, request_rework, reject. "
            "No selected parity claim is supported until completed review results are ingested.\n",
            encoding="utf-8",
        )
        (out_dir / "operator_handoff_readme.md").write_text(
            "# S13c evidence packet handoff\n\n"
            "This packet was built from S13b public_api_dev GigaChat live outputs. "
            "It is not Server 3 local_intranet proof and it does not contain completed human review results.\n",
            encoding="utf-8",
        )
        archive_manifest = {
            "status": status,
            "packet_index": "packet_index.json",
            "artifact_file_count": len(list(out_dir.rglob("*"))),
            "credential_values_recorded": False,
            "raw_secret_values_recorded": False,
        }
        _write_json(out_dir / "archive_manifest.json", archive_manifest)
        return packet_index


def zip_packet(packet_dir: Path, zip_out: Path) -> None:
    zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(packet_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(packet_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Export S13c human-review evidence packet from S13b live GigaChat outputs.")
    parser.add_argument("--s13b-live-input", type=Path, required=True, help="S13b live ZIP or extracted artifacts directory")
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.packet_dir.exists():
        shutil.rmtree(args.packet_dir)
    report = build_packet(args.s13b_live_input.resolve(), args.packet_dir.resolve())
    zip_packet(args.packet_dir.resolve(), args.zip_out.resolve())
    report["zip_out"] = str(args.zip_out.resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S13c evidence packet export: {report['status']}")
        print(f"zip: {args.zip_out}")
    return 0 if report.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
