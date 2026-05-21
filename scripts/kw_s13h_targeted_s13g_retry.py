#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import ssl
import sys
import tempfile
import time
import uuid
import zipfile
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.canonical_schema_adapter import (
    adapt_minimal_model_payload_to_canonical,
    minimal_prompt_for_scenario,
    validate_canonical_s13g_payload,
)
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.targeted_s13g_retry import KNOWN_FAILED_S13G_SCENARIOS

DEFAULT_ENDPOINT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
DEFAULT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
DEFAULT_MODEL = "GigaChat"
DEFAULT_SCOPE = "GIGACHAT_API_PERS"
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


def json_digest(payload: object) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def digest_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def ssl_context() -> ssl.SSLContext | None:
    return ssl._create_unverified_context() if os.environ.get("KW_RC3_GIGACHAT_SSL_VERIFY", "1").lower() in {"0", "false", "no"} else None


def configured_secret_names() -> list[str]:
    return [name for name in SECRET_ENV_NAMES if os.environ.get(name, "").strip()]


def read_json_response(request: Request, timeout: float) -> dict[str, object]:
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def get_access_token(timeout: float) -> tuple[str, str]:
    direct = os.environ.get("KW_RC3_GIGACHAT_ACCESS_TOKEN") or os.environ.get("KW_RC3_GIGACHAT_BEARER") or os.environ.get("GIGACHAT_ACCESS_TOKEN")
    if direct and direct.strip():
        return direct.strip().removeprefix("Bearer ").strip(), "access_token_env"
    auth_key = os.environ.get("KW_RC3_GIGACHAT_AUTHORIZATION_KEY") or os.environ.get("KW_RC3_GIGACHAT_AUTH_KEY") or os.environ.get("GIGACHAT_CREDENTIALS")
    client_id = os.environ.get("KW_RC3_GIGACHAT_CLIENT_ID")
    client_secret = os.environ.get("KW_RC3_GIGACHAT_CLIENT_SECRET")
    if auth_key and auth_key.strip():
        authorization = auth_key.strip()
        if not authorization.lower().startswith("basic "):
            authorization = "Basic " + authorization
        source = "authorization_key_env"
    elif client_id and client_secret:
        authorization = "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("ascii")
        source = "client_id_client_secret_env"
    else:
        raise RuntimeError("S13h targeted retry requires GigaChat credentials in shell env.")
    req = Request(
        os.environ.get("KW_RC3_GIGACHAT_AUTH_URL", DEFAULT_AUTH_URL),
        data=f"scope={os.environ.get('KW_RC3_GIGACHAT_SCOPE', DEFAULT_SCOPE)}".encode(),
        method="POST",
        headers={
            "Authorization": authorization,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        },
    )
    payload = read_json_response(req, timeout)
    token = str(payload.get("access_token") or payload.get("accessToken") or "").strip()
    if not token:
        raise RuntimeError("GigaChat OAuth response did not include access_token.")
    return token, source


def call_gigachat(prompt: str, token: str, timeout: float, model: str) -> dict[str, object]:
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
    req = Request(
        os.environ.get("KW_RC3_GIGACHAT_ENDPOINT", DEFAULT_ENDPOINT),
        data=json.dumps(payload, ensure_ascii=False).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        },
    )
    return read_json_response(req, timeout)


def extract_text(response: dict[str, object]) -> str:
    try:
        return str(response["choices"][0]["message"]["content"])
    except Exception:
        return ""


def parse_jsonish(text: str) -> tuple[object | None, list[str], str | None]:
    candidate = text.strip()
    actions: list[str] = []
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json|JSON)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
        actions.append("strip_markdown_code_fences")
    candidate = "".join(" " if ord(ch) < 32 and ch not in "\t\r\n" else ch for ch in candidate)
    try:
        return json.loads(candidate), actions, None
    except json.JSONDecodeError:
        try:
            payload, end = json.JSONDecoder().raw_decode(candidate)
            if candidate[end:].strip():
                actions.append("trim_trailing_extra_data")
            actions.append("json_raw_decode_first_object")
            return payload, actions, None
        except json.JSONDecodeError as exc:
            return None, actions, str(exc)


def extract_zip(zip_path: Path, work_dir: Path) -> Path:
    out = work_dir / "input"
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out)
    return out


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_s13g_manifest(root: Path) -> Path:
    matches = sorted(root.rglob("s13g_canonical_adapter_live_generation_manifest.json"))
    if not matches:
        matches = sorted(root.rglob("s13g-canonical-adapter-live-generation.json"))
    if not matches:
        raise RuntimeError("S13h requires an S13g live manifest")
    return matches[0]


def find_scenario_file(root: Path, scenario_id: str) -> Path | None:
    matches = sorted(root.rglob(f"*_{scenario_id}_canonical_adapter_response.json"))
    return matches[0] if matches else None


def retry_one_scenario(scenario_id: str, *, token: str, timeout: float, model: str) -> tuple[dict[str, Any], list[str]]:
    response = call_gigachat(minimal_prompt_for_scenario(scenario_id), token, timeout, model)
    text = extract_text(response)
    parsed, parse_actions, parse_error = parse_jsonish(text)
    errors: list[str] = []
    canonical_payload = None
    adapter_error = None
    if parse_error is None:
        try:
            canonical_payload = adapt_minimal_model_payload_to_canonical(parsed, scenario_id)
            errors = validate_canonical_s13g_payload(canonical_payload, scenario_id)
        except Exception as exc:
            adapter_error = f"{type(exc).__name__}: {str(exc)[:240]}"
            errors = ["canonical_adapter_failed"]
    else:
        errors = ["json_parse_failed"]
    metadata = {
        "scenario_id": scenario_id,
        "provider": REQUIRED_PROVIDER,
        "route": PUBLIC_API_DEV_ROUTE,
        "model": model,
        "targeted_retry_performed": True,
        "response_text_present": bool(text.strip()),
        "response_text_length": len(text),
        "parse_actions_applied": parse_actions,
        "parse_error": parse_error,
        "adapter_error": adapter_error,
        "canonical_schema_valid": parse_error is None and not errors,
        "canonical_schema_errors": errors,
        "adapter_provenance_present": isinstance(canonical_payload, dict) and isinstance(canonical_payload.get("adapter_provenance"), dict),
        "adapter_fields_are_not_model_generated": bool(
            isinstance(canonical_payload, dict)
            and isinstance(canonical_payload.get("adapter_provenance"), dict)
            and canonical_payload["adapter_provenance"].get("adapter_fields_are_not_model_generated") is True
        ),
        "completed_human_review_results_present": False,
        "auto_approval_allowed": False,
        "selected_offline_workflow_parity_claim_supported_now": False,
        "kimi_level_claimed": False,
        "server3_local_intranet_route_verified": False,
        "raw_secret_values_recorded": False,
        "prompt_digest": json_digest(minimal_prompt_for_scenario(scenario_id)),
        "response_digest": json_digest(response),
        "model_payload_digest": json_digest(parsed) if parsed is not None else None,
        "canonical_payload_digest": json_digest(canonical_payload) if canonical_payload is not None else None,
        "parsed_model_payload": parsed,
        "canonical_payload": canonical_payload,
        "response": response,
    }
    return metadata, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Retry only failed S13g canonical adapter scenarios and merge with prior canonical-valid outputs.")
    parser.add_argument("--s13g-live-input", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, required=True)
    parser.add_argument("--retry-scenarios", nargs="*", default=list(KNOWN_FAILED_S13G_SCENARIOS))
    parser.add_argument("--require-all-canonical-valid", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    started = time.time()
    artifacts_dir = args.artifacts_dir.resolve()
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    timeout = float(os.environ.get("KW_RC3_GIGACHAT_TIMEOUT_SECONDS", "120"))
    model = os.environ.get("KW_RC3_GIGACHAT_MODEL", DEFAULT_MODEL)
    retry_scenarios = tuple(args.retry_scenarios or KNOWN_FAILED_S13G_SCENARIOS)
    errors: list[str] = []
    scenario_results: list[dict[str, Any]] = []
    token_source = None

    with tempfile.TemporaryDirectory(prefix="s13h-s13g-input-") as tmp:
        input_root = extract_zip(args.s13g_live_input.resolve(), Path(tmp)) if args.s13g_live_input.is_file() else args.s13g_live_input.resolve()
        manifest_path = find_s13g_manifest(input_root)
        source_manifest = load_json(manifest_path)
        if source_manifest.get("route") != PUBLIC_API_DEV_ROUTE:
            raise RuntimeError("S13g manifest route must be public_api_dev")
        if int(source_manifest.get("successful_scenario_generation_count") or 0) < 10:
            raise RuntimeError("S13h requires a prior S13g run with reusable canonical outputs")
        if source_manifest.get("credential_values_recorded") is not False or source_manifest.get("raw_secret_values_recorded") is not False:
            raise RuntimeError("S13g manifest must not record credential values")

        try:
            token, token_source = get_access_token(timeout)
        except Exception as exc:
            token = ""
            errors.append(str(exc))

        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            out_path = artifacts_dir / f"s13h_{index:02d}_{scenario_id}_merged_canonical_response.json"
            if scenario_id not in retry_scenarios:
                prior_file = find_scenario_file(input_root, scenario_id)
                if prior_file is None:
                    errors.append(f"{scenario_id}: missing prior S13g response file")
                    continue
                prior = load_json(prior_file)
                if prior.get("canonical_schema_valid") is not True:
                    errors.append(f"{scenario_id}: prior S13g output is not canonical-valid and was not selected for retry")
                prior["s13h_reuse_prior_canonical_output"] = True
                prior["s13h_source_prior_file"] = prior_file.name
                prior["s13h_source_prior_file_digest"] = digest_file(prior_file)
                prior["completed_human_review_results_present"] = False
                prior["selected_offline_workflow_parity_claim_supported_now"] = False
                prior["server3_local_intranet_route_verified"] = False
                prior["kimi_level_claimed"] = False
                out_path.write_text(json.dumps(prior, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
                scenario_results.append({
                    "scenario_id": scenario_id,
                    "source": "reused_prior_s13g_canonical_valid_output",
                    "canonical_schema_valid": prior.get("canonical_schema_valid") is True,
                    "canonical_payload_digest": prior.get("canonical_payload_digest"),
                })
                continue

            if not token:
                errors.append(f"{scenario_id}: retry requires GigaChat token")
                continue
            try:
                retry_payload, retry_errors = retry_one_scenario(scenario_id, token=token, timeout=timeout, model=model)
                out_path.write_text(json.dumps(retry_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
                scenario_results.append({
                    "scenario_id": scenario_id,
                    "source": "targeted_s13h_live_retry",
                    "canonical_schema_valid": retry_payload.get("canonical_schema_valid") is True,
                    "canonical_payload_digest": retry_payload.get("canonical_payload_digest"),
                    "retry_errors": retry_errors,
                })
                if retry_errors:
                    errors.append(f"{scenario_id}: targeted retry canonical validation failed: {'; '.join(retry_errors[:4])}")
            except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
                errors.append(f"{scenario_id}: {type(exc).__name__}: {str(exc)[:240]}")

    canonical_valid_count = sum(1 for item in scenario_results if item.get("canonical_schema_valid") is True)
    retried_valid_count = sum(1 for item in scenario_results if item.get("source") == "targeted_s13h_live_retry" and item.get("canonical_schema_valid") is True)
    reused_count = sum(1 for item in scenario_results if item.get("source") == "reused_prior_s13g_canonical_valid_output")

    if args.require_all_canonical_valid and canonical_valid_count != len(S10_SCENARIO_IDS):
        errors.append(f"expected all {len(S10_SCENARIO_IDS)} scenarios canonical-valid after S13h merge, got {canonical_valid_count}")

    manifest = {
        "workflow_id": "slides.targeted_retry_failed_s13g_scenarios",
        "s_phase": "S13h-live",
        "status": "ready" if not errors else "failed",
        "provider": REQUIRED_PROVIDER,
        "route": PUBLIC_API_DEV_ROUTE,
        "model": model,
        "scenario_count": len(S10_SCENARIO_IDS),
        "retry_scenario_ids": list(retry_scenarios),
        "retry_scenario_count": len(retry_scenarios),
        "reused_canonical_scenario_count": reused_count,
        "canonical_schema_valid_scenario_count_after_merge": canonical_valid_count,
        "retried_canonical_valid_scenario_count": retried_valid_count,
        "targeted_retry_performed_by_s13h_live": retried_valid_count > 0,
        "credential_input_names_configured": configured_secret_names(),
        "credential_source": token_source,
        "credential_values_recorded": False,
        "raw_secret_values_recorded": False,
        "server3_local_intranet_route_verified_by_s13h_live": False,
        "public_api_dev_route_is_not_server3_proof": True,
        "completed_human_review_results_present_by_s13h_live": False,
        "auto_approval_allowed_by_s13h_live": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13h_live": False,
        "kimi_level_claimed_by_s13h_live": False,
        "whole_project_kimi_level_supported": False,
        "artifacts_dir": str(artifacts_dir),
        "scenario_results": scenario_results,
        "elapsed_seconds": round(time.time() - started, 3),
        "errors": errors,
    }
    (artifacts_dir / "s13h_targeted_retry_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")

    args.zip_out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.zip_out.resolve(), "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(artifacts_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(artifacts_dir))
    manifest["zip_out"] = str(args.zip_out.resolve())

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13h targeted retry: {manifest['status']}")
        print(f"canonical valid after merge: {canonical_valid_count}/{len(S10_SCENARIO_IDS)}")
        for error in errors:
            print(f"- {error}")
    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
