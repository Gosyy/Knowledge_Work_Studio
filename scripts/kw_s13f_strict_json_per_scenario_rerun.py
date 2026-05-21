#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, os, re, ssl, sys, time, uuid
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.strict_json_per_scenario_rerun import strict_json_prompt_for_scenario, validate_strict_s13f_payload
DEFAULT_ENDPOINT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
DEFAULT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
DEFAULT_MODEL = "GigaChat"
DEFAULT_SCOPE = "GIGACHAT_API_PERS"
SECRET_ENV_NAMES = ("KW_RC3_GIGACHAT_AUTHORIZATION_KEY", "KW_RC3_GIGACHAT_AUTH_KEY", "GIGACHAT_CREDENTIALS", "KW_RC3_GIGACHAT_CLIENT_ID", "KW_RC3_GIGACHAT_CLIENT_SECRET", "KW_RC3_GIGACHAT_ACCESS_TOKEN", "KW_RC3_GIGACHAT_BEARER", "GIGACHAT_ACCESS_TOKEN")

def _json_digest(payload: object) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()

def _ssl_context():
    return ssl._create_unverified_context() if os.environ.get("KW_RC3_GIGACHAT_SSL_VERIFY", "1").lower() in {"0", "false", "no"} else None

def _configured_secret_names() -> list[str]:
    return [name for name in SECRET_ENV_NAMES if os.environ.get(name, "").strip()]

def _read_json_response(request: Request, timeout: float) -> dict[str, object]:
    with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))

def _get_access_token(timeout: float) -> tuple[str, str]:
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
        raise RuntimeError("S13f strict rerun requires GigaChat credentials in shell env.")
    req = Request(os.environ.get("KW_RC3_GIGACHAT_AUTH_URL", DEFAULT_AUTH_URL), data=f"scope={os.environ.get('KW_RC3_GIGACHAT_SCOPE', DEFAULT_SCOPE)}".encode(), method="POST", headers={"Authorization": authorization, "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json", "RqUID": str(uuid.uuid4())})
    payload = _read_json_response(req, timeout)
    token = str(payload.get("access_token") or payload.get("accessToken") or "").strip()
    if not token:
        raise RuntimeError("GigaChat OAuth response did not include access_token.")
    return token, source

def _call(prompt: str, token: str, timeout: float, model: str) -> dict[str, object]:
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
    req = Request(os.environ.get("KW_RC3_GIGACHAT_ENDPOINT", DEFAULT_ENDPOINT), data=json.dumps(payload, ensure_ascii=False).encode(), method="POST", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json", "RqUID": str(uuid.uuid4())})
    return _read_json_response(req, timeout)

def _extract_text(response: dict[str, object]) -> str:
    try:
        return str(response["choices"][0]["message"]["content"])
    except Exception:
        return ""

def _parse_jsonish(text: str):
    candidate = text.strip()
    actions = []
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

def main() -> int:
    parser = argparse.ArgumentParser(description="Run S13f strict per-scenario public_api_dev GigaChat rerun.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--require-all-scenarios", action="store_true")
    parser.add_argument("--require-schema-valid", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    artifacts_dir = args.artifacts_dir.resolve(); artifacts_dir.mkdir(parents=True, exist_ok=True)
    timeout = float(os.environ.get("KW_RC3_GIGACHAT_TIMEOUT_SECONDS", "120")); model = os.environ.get("KW_RC3_GIGACHAT_MODEL", DEFAULT_MODEL)
    errors = []; results = []; token_source = None; started = time.time()
    try:
        token, token_source = _get_access_token(timeout)
    except Exception as exc:
        token = ""; errors.append(str(exc))
    if token:
        for index, scenario_id in enumerate(S10_SCENARIO_IDS, 1):
            try:
                prompt = strict_json_prompt_for_scenario(scenario_id)
                response = _call(prompt, token, timeout, model)
                text = _extract_text(response)
                parsed, repair_actions, parse_error = _parse_jsonish(text)
                schema_errors = validate_strict_s13f_payload(parsed, scenario_id) if parse_error is None else ["json_parse_failed"]
                schema_valid = parse_error is None and not schema_errors
                payload = {"scenario_id": scenario_id, "provider": REQUIRED_PROVIDER, "route": PUBLIC_API_DEV_ROUTE, "model": model, "strict_public_api_dev_execution_performed": True, "response_text_present": bool(text.strip()), "response_text_length": len(text), "schema_valid": schema_valid, "schema_errors": schema_errors, "parse_error": parse_error, "repair_fallback_applied": bool(repair_actions), "repair_actions_applied": repair_actions, "completed_human_review_results_present": False, "auto_approval_allowed": False, "selected_offline_workflow_parity_claim_supported_now": False, "kimi_level_claimed": False, "server3_local_intranet_route_verified": False, "raw_secret_values_recorded": False, "prompt_digest": _json_digest(prompt), "response_digest": _json_digest(response), "parsed_or_repaired_payload": parsed, "response": response}
                (artifacts_dir / f"s13f_{index:02d}_{scenario_id}_strict_gigachat_response.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
                results.append({k: v for k, v in payload.items() if k not in {"response", "parsed_or_repaired_payload"}})
                if args.require_schema_valid and not schema_valid:
                    errors.append(f"{scenario_id}: strict schema validation failed: {'; '.join(schema_errors[:4]) or parse_error}")
            except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
                errors.append(f"{scenario_id}: {type(exc).__name__}: {str(exc)[:240]}")
    success = sum(1 for item in results if item.get("response_text_present") is True)
    valid = sum(1 for item in results if item.get("schema_valid") is True)
    if args.require_all_scenarios and success != len(S10_SCENARIO_IDS):
        errors.append(f"expected successful responses for all {len(S10_SCENARIO_IDS)} scenarios, got {success}")
    manifest = {"workflow_id": "slides.strict_json_per_scenario_rerun", "s_phase": "S13f-live", "status": "ready" if not errors else "failed", "provider": REQUIRED_PROVIDER, "route": PUBLIC_API_DEV_ROUTE, "model": model, "scenario_count": len(S10_SCENARIO_IDS), "successful_scenario_generation_count": success, "schema_valid_scenario_count": valid, "strict_public_api_dev_execution_performed_by_s13f_live": success > 0, "repair_fallback_available_by_s13f_live": True, "credential_input_names_configured": _configured_secret_names(), "credential_source": token_source, "credential_values_recorded": False, "raw_secret_values_recorded": False, "server3_local_intranet_route_verified_by_s13f_live": False, "public_api_dev_route_is_not_server3_proof": True, "completed_human_review_results_present_by_s13f_live": False, "auto_approval_allowed_by_s13f_live": False, "selected_offline_workflow_parity_claim_supported_now_by_s13f_live": False, "kimi_level_claimed_by_s13f_live": False, "whole_project_kimi_level_supported": False, "artifacts_dir": str(artifacts_dir), "scenario_results": results, "elapsed_seconds": round(time.time() - started, 3), "errors": errors}
    (artifacts_dir / "s13f_strict_live_generation_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"S13f strict public_api_dev GigaChat rerun: {manifest['status']}")
        print(f"Successful scenarios: {success}/{len(S10_SCENARIO_IDS)}")
        print(f"Schema-valid scenarios: {valid}/{len(S10_SCENARIO_IDS)}")
        for error in errors: print(f"- {error}")
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
