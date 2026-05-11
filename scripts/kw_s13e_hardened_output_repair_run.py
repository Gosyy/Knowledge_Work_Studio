#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from hashlib import sha256
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.hardened_output_repair import repair_hardened_response_text
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER


def digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def digest_json(payload: Any) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_zip(zip_path: Path, work_dir: Path) -> Path:
    out = work_dir / "input"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out)
    return out


def find_manifest(root: Path) -> Path:
    matches = sorted(root.rglob("s13d_hardened_live_generation_manifest.json"))
    if not matches:
        matches = sorted(root.rglob("s13d-hardened-live-generation.json"))
    if not matches:
        raise RuntimeError("S13e requires s13d_hardened_live_generation_manifest.json or s13d-hardened-live-generation.json")
    return matches[0]


def scenario_response_file(root: Path, scenario_id: str) -> Path | None:
    matches = sorted(root.rglob(f"*_{scenario_id}_hardened_gigachat_response.json"))
    return matches[0] if matches else None


def extract_response_text(payload: dict[str, Any]) -> str:
    response = payload.get("response")
    if isinstance(response, dict):
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return str(message["content"])
    parsed = payload.get("parsed_payload")
    if isinstance(parsed, dict):
        return json.dumps(parsed, ensure_ascii=False)
    return ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def build_repair_packet(input_path: Path, repaired_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="s13e-hardened-input-") as tmp:
        tmp_path = Path(tmp)
        if input_path.is_file() and input_path.suffix == ".zip":
            input_root = extract_zip(input_path, tmp_path)
        elif input_path.is_dir():
            input_root = input_path
        else:
            raise RuntimeError("--s13d-live-input must be a ZIP archive or extracted S13d artifacts directory")

        manifest_path = find_manifest(input_root)
        source_manifest = load_json(manifest_path)
        if source_manifest.get("route") != PUBLIC_API_DEV_ROUTE:
            raise RuntimeError("S13d manifest route must be public_api_dev")
        if int(source_manifest.get("successful_scenario_generation_count") or 0) != 12:
            raise RuntimeError("S13d manifest must include 12 successful scenario generations")
        if source_manifest.get("credential_values_recorded") is not False or source_manifest.get("raw_secret_values_recorded") is not False:
            raise RuntimeError("S13d manifest must not record credential values")

        if repaired_dir.exists():
            shutil.rmtree(repaired_dir)
        repaired_dir.mkdir(parents=True, exist_ok=True)
        scenarios_dir = repaired_dir / "scenarios"
        repair_entries: list[dict[str, Any]] = []
        errors: list[str] = []

        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            response_path = scenario_response_file(input_root, scenario_id)
            if response_path is None:
                errors.append(f"{scenario_id}: missing S13d response file")
                continue
            original_payload = load_json(response_path)
            text = extract_response_text(original_payload)
            result = repair_hardened_response_text(text, scenario_id)
            output_payload = {
                "scenario_id": scenario_id,
                "provider": original_payload.get("provider", REQUIRED_PROVIDER),
                "route": original_payload.get("route", PUBLIC_API_DEV_ROUTE),
                "original_response_file": response_path.name,
                "original_response_file_digest": digest_file(response_path),
                "original_response_digest": original_payload.get("response_digest"),
                "repair_status": result.status,
                "schema_valid_after_repair": result.schema_valid,
                "repair_actions_applied": list(result.repair_actions_applied),
                "parse_error": result.parse_error,
                "schema_errors": list(result.schema_errors),
                "repaired_payload_digest": digest_json(result.repaired_payload) if result.repaired_payload is not None else None,
                "completed_human_review_results_present": False,
                "auto_approval_allowed": False,
                "selected_offline_workflow_parity_claim_supported_now": False,
                "server3_local_intranet_route_verified": False,
                "kimi_level_claimed": False,
                "raw_secret_values_recorded": False,
                "repaired_payload": result.repaired_payload,
            }
            write_json(scenarios_dir / f"s13e_{index:02d}_{scenario_id}_repaired_payload.json", output_payload)
            repair_entries.append({k: v for k, v in output_payload.items() if k != "repaired_payload"})
            if not result.schema_valid:
                errors.append(f"{scenario_id}: schema invalid after repair: {'; '.join(result.schema_errors[:5])}")

        schema_valid_count = sum(1 for item in repair_entries if item.get("schema_valid_after_repair") is True)
        report = {
            "workflow_id": "slides.hardened_output_repair_parser",
            "s_phase": "S13e-execution",
            "status": "ready" if not errors else "failed",
            "provider": REQUIRED_PROVIDER,
            "route": PUBLIC_API_DEV_ROUTE,
            "scenario_count": len(S10_SCENARIO_IDS),
            "successful_scenario_generation_count_from_s13d": int(source_manifest.get("successful_scenario_generation_count") or 0),
            "schema_valid_scenario_count_after_repair": schema_valid_count,
            "repair_attempted_scenario_count": len(repair_entries),
            "deterministic_repair_only": True,
            "live_gigachat_call_allowed_by_s13e": False,
            "credential_values_recorded": False,
            "raw_secret_values_recorded": False,
            "completed_human_review_results_present": False,
            "auto_approval_allowed": False,
            "selected_offline_workflow_parity_claim_supported_now": False,
            "server3_local_intranet_route_verified": False,
            "public_api_dev_route_is_not_server3_proof": True,
            "kimi_level_claimed": False,
            "source_manifest": manifest_path.name,
            "source_manifest_digest": digest_file(manifest_path),
            "repair_results": repair_entries,
            "errors": errors,
        }
        write_json(repaired_dir / "s13e_repair_manifest.json", report)
        return report


def zip_dir(src: Path, zip_out: Path) -> None:
    zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(src))


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair and revalidate S13d hardened live GigaChat outputs without calling GigaChat.")
    parser.add_argument("--s13d-live-input", type=Path, required=True)
    parser.add_argument("--repaired-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, required=True)
    parser.add_argument("--require-all-schema-valid", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_repair_packet(args.s13d_live_input.resolve(), args.repaired_dir.resolve())
    zip_dir(args.repaired_dir.resolve(), args.zip_out.resolve())
    report["zip_out"] = str(args.zip_out.resolve())
    if args.require_all_schema_valid and report.get("schema_valid_scenario_count_after_repair") != report.get("scenario_count"):
        report["status"] = "failed"
        report.setdefault("errors", []).append(
            f"expected all {report.get('scenario_count')} scenarios schema-valid after repair, got {report.get('schema_valid_scenario_count_after_repair')}"
        )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13e hardened output repair: {report['status']}")
        print(f"schema valid after repair: {report['schema_valid_scenario_count_after_repair']}/{report['scenario_count']}")
        for error in report.get("errors", []):
            print(f"- {error}")
    return 0 if report.get("status") == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
