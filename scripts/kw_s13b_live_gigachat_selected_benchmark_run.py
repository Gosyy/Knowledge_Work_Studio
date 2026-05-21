#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import time
import uuid
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS  # noqa: E402
from backend.app.services.slides_service.live_gigachat_selected_benchmark import (  # noqa: E402
    PUBLIC_API_DEV_ROUTE,
    REQUIRED_PROVIDER,
    REQUIRED_LIVE_OUTPUTS,
)

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


def _json_digest(payload: object) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _ssl_context() -> ssl.SSLContext | None:
    verify = os.environ.get("KW_RC3_GIGACHAT_SSL_VERIFY", "1").strip().lower()
    if verify in {"0", "false", "no"}:
        return ssl._create_unverified_context()  # noqa: SLF001 - explicit dev/public-api override
    return None


def _configured_secret_names() -> list[str]:
    return [name for name in SECRET_ENV_NAMES if os.environ.get(name, "").strip()]


def _read_json_response(request: Request, *, timeout: float) -> dict[str, object]:
    with urlopen(request, timeout=timeout, context=_ssl_context()) as response:  # nosec - endpoint is explicit operator config
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def _get_access_token(timeout: float) -> tuple[str, str]:
    direct_token = os.environ.get("KW_RC3_GIGACHAT_ACCESS_TOKEN") or os.environ.get("KW_RC3_GIGACHAT_BEARER") or os.environ.get("GIGACHAT_ACCESS_TOKEN")
    if direct_token and direct_token.strip():
        return direct_token.strip().removeprefix("Bearer ").strip(), "access_token_env"

    auth_key = (
        os.environ.get("KW_RC3_GIGACHAT_AUTHORIZATION_KEY")
        or os.environ.get("KW_RC3_GIGACHAT_AUTH_KEY")
        or os.environ.get("GIGACHAT_CREDENTIALS")
    )
    client_id = os.environ.get("KW_RC3_GIGACHAT_CLIENT_ID")
    client_secret = os.environ.get("KW_RC3_GIGACHAT_CLIENT_SECRET")
    if auth_key and auth_key.strip():
        authorization = auth_key.strip()
        if not authorization.lower().startswith("basic "):
            authorization = "Basic " + authorization
        credential_source = "authorization_key_env"
    elif client_id and client_secret:
        encoded = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        authorization = "Basic " + encoded
        credential_source = "client_id_client_secret_env"
    else:
        raise RuntimeError("S13b live run requires KW_RC3_GIGACHAT_AUTHORIZATION_KEY or KW_RC3_GIGACHAT_CLIENT_ID/KW_RC3_GIGACHAT_CLIENT_SECRET or access token in shell env.")

    auth_url = os.environ.get("KW_RC3_GIGACHAT_AUTH_URL", DEFAULT_AUTH_URL)
    scope = os.environ.get("KW_RC3_GIGACHAT_SCOPE", DEFAULT_SCOPE)
    body = f"scope={scope}".encode("utf-8")
    request = Request(
        auth_url,
        data=body,
        method="POST",
        headers={
            "Authorization": authorization,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        },
    )
    payload = _read_json_response(request, timeout=timeout)
    token = str(payload.get("access_token") or payload.get("accessToken") or "").strip()
    if not token:
        raise RuntimeError("GigaChat OAuth response did not include access_token.")
    return token, credential_source


def _scenario_prompt(scenario_id: str) -> str:
    return (
        "You are generating a strict KW Studio S13b selected benchmark execution plan. "
        "Return concise JSON-compatible text only. "
        f"Scenario: {scenario_id}. "
        "Include: outline intent, slide archetype intent, required evidence outputs, citation obligations, render QA obligations, and human review handoff. "
        "Do not claim Kimi-level, do not claim Server 3 local_intranet verification, and do not approve the scenario."
    )


def _call_gigachat(prompt: str, *, token: str, timeout: float, model: str) -> dict[str, object]:
    endpoint = os.environ.get("KW_RC3_GIGACHAT_ENDPOINT", DEFAULT_ENDPOINT)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        endpoint,
        data=data,
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        },
    )
    return _read_json_response(request, timeout=timeout)


def _extract_text(response: dict[str, object]) -> str:
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run S13b live public_api_dev GigaChat generation for 12 selected benchmark scenarios.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--require-all-scenarios", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts_dir = args.artifacts_dir.resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    timeout = float(os.environ.get("KW_RC3_GIGACHAT_TIMEOUT_SECONDS", "120"))
    model = os.environ.get("KW_RC3_GIGACHAT_MODEL", DEFAULT_MODEL)
    started = time.time()
    errors: list[str] = []
    scenario_results: list[dict[str, object]] = []
    token_source = None

    try:
        token, token_source = _get_access_token(timeout)
    except Exception as exc:  # pragma: no cover - operator live env boundary
        errors.append(str(exc))
        token = ""

    if token:
        for index, scenario_id in enumerate(S10_SCENARIO_IDS, start=1):
            scenario_file = artifacts_dir / f"s13b_{index:02d}_{scenario_id}_gigachat_response.json"
            try:
                response = _call_gigachat(_scenario_prompt(scenario_id), token=token, timeout=timeout, model=model)
                text = _extract_text(response)
                scenario_payload = {
                    "scenario_id": scenario_id,
                    "provider": REQUIRED_PROVIDER,
                    "route": PUBLIC_API_DEV_ROUTE,
                    "model": model,
                    "public_api_dev_execution_performed": True,
                    "response_text_present": bool(text.strip()),
                    "response_text_length": len(text),
                    "required_live_outputs": list(REQUIRED_LIVE_OUTPUTS),
                    "completed_human_review_results_present": False,
                    "auto_approval_allowed": False,
                    "selected_offline_workflow_parity_claim_supported_now": False,
                    "kimi_level_claimed": False,
                    "server3_local_intranet_route_verified": False,
                    "raw_secret_values_recorded": False,
                    "response_digest": _json_digest(response),
                    "response": response,
                }
                scenario_file.write_text(json.dumps(scenario_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
                scenario_results.append({k: v for k, v in scenario_payload.items() if k != "response"})
                if not text.strip():
                    errors.append(f"{scenario_id}: empty GigaChat response text")
            except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
                errors.append(f"{scenario_id}: {type(exc).__name__}: {str(exc)[:240]}")

    success_count = sum(1 for item in scenario_results if item.get("response_text_present") is True)
    if args.require_all_scenarios and success_count != len(S10_SCENARIO_IDS):
        errors.append(f"expected successful GigaChat responses for all {len(S10_SCENARIO_IDS)} scenarios, got {success_count}")

    manifest = {
        "workflow_id": "slides.live_public_api_dev_gigachat_generation",
        "s_phase": "S13b-live",
        "status": "ready" if not errors else "failed",
        "provider": REQUIRED_PROVIDER,
        "route": PUBLIC_API_DEV_ROUTE,
        "model": model,
        "scenario_count": len(S10_SCENARIO_IDS),
        "successful_scenario_generation_count": success_count,
        "public_api_dev_execution_performed_by_s13b_live": success_count > 0,
        "credential_input_names_configured": _configured_secret_names(),
        "credential_source": token_source,
        "credential_values_recorded": False,
        "raw_secret_values_recorded": False,
        "server3_local_intranet_route_verified_by_s13b_live": False,
        "public_api_dev_route_is_not_server3_proof": True,
        "completed_human_review_results_present_by_s13b_live": False,
        "auto_approval_allowed_by_s13b_live": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13b_live": False,
        "kimi_level_claimed_by_s13b_live": False,
        "whole_project_kimi_level_supported": False,
        "artifacts_dir": str(artifacts_dir),
        "scenario_results": scenario_results,
        "elapsed_seconds": round(time.time() - started, 3),
        "errors": errors,
    }
    (artifacts_dir / "s13b_live_generation_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"S13b live public_api_dev GigaChat generation: {manifest['status']}")
        print(f"Successful scenarios: {success_count}/{len(S10_SCENARIO_IDS)}")
        for error in errors:
            print(f"- {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
