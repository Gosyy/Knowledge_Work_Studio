#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    payload: Any
    raw_text: str


def request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: float = 10.0) -> HttpResult:
    body: bytes | None = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return HttpResult(status_code=response.status, payload=json.loads(raw or "{}"), raw_text=raw)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload_obj: Any = json.loads(raw or "{}")
        except json.JSONDecodeError:
            payload_obj = {"raw": raw}
        return HttpResult(status_code=exc.code, payload=payload_obj, raw_text=raw)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def endpoint(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def run_backend_smoke(base_url: str, *, timeout: float, strict_ready: bool, skip_session: bool) -> None:
    print(f"[INFO] backend={base_url}")

    health = request_json(endpoint(base_url, "/health"), timeout=timeout)
    print(f"[health] status={health.status_code} payload={health.payload}")
    expect(health.status_code == 200, "GET /health must return 200")
    expect(health.payload.get("status") == "ok", "GET /health must return {'status': 'ok'}")

    ready = request_json(endpoint(base_url, "/ready"), timeout=timeout)
    print(f"[ready] status={ready.status_code} payload={json.dumps(ready.payload, sort_keys=True)}")
    if strict_ready:
        expect(ready.status_code == 200, "GET /ready must return 200 in strict mode")
        expect(ready.payload.get("status") == "ready", "GET /ready must be ready in strict mode")
    else:
        expect(ready.status_code in {200, 503}, "GET /ready must return either 200 or 503")

    if skip_session:
        return

    session = request_json(endpoint(base_url, "/sessions"), method="POST", payload={}, timeout=timeout)
    print(f"[sessions] status={session.status_code} payload={session.payload}")
    expect(session.status_code == 201, "POST /sessions must return 201")
    session_id = session.payload.get("id")
    expect(isinstance(session_id, str) and session_id, "POST /sessions must return an id")

    presentations = request_json(endpoint(base_url, f"/sessions/{session_id}/presentations"), timeout=timeout)
    print(f"[presentations] status={presentations.status_code} payload={presentations.payload}")
    expect(presentations.status_code == 200, "GET /sessions/{id}/presentations must return 200")
    expect(isinstance(presentations.payload, list), "Presentation registry endpoint must return a list")


def run_frontend_http_smoke(frontend_url: str, *, timeout: float) -> None:
    req = request.Request(frontend_url.rstrip("/"), method="GET", headers={"Accept": "text/html"})
    with request.urlopen(req, timeout=timeout) as response:
        raw = response.read(4096).decode("utf-8", errors="replace")
        print(f"[frontend] status={response.status} first_bytes={len(raw)}")
        expect(response.status == 200, "frontend root must return 200")
        expect("<html" in raw.lower() or "__next" in raw.lower(), "frontend root should look like a Next.js HTML page")


def main() -> int:
    parser = argparse.ArgumentParser(description="KW Studio operator smoke checks against a running deployment.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL.")
    parser.add_argument("--frontend-url", default="", help="Optional frontend URL to smoke-check.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds.")
    parser.add_argument("--strict-ready", action="store_true", help="Require /ready to return ready/200.")
    parser.add_argument("--skip-session", action="store_true", help="Skip mutating session creation smoke.")
    parser.add_argument("--retries", type=int, default=1, help="Retry count for transient startup windows.")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="Delay between retries.")
    args = parser.parse_args()

    last_error: Exception | None = None
    for attempt in range(1, max(1, args.retries) + 1):
        try:
            print(f"[INFO] smoke attempt {attempt}/{max(1, args.retries)}")
            run_backend_smoke(
                args.base_url,
                timeout=args.timeout,
                strict_ready=args.strict_ready,
                skip_session=args.skip_session,
            )
            if args.frontend_url:
                run_frontend_http_smoke(args.frontend_url, timeout=args.timeout)
            print("[PASS] operator smoke completed")
            return 0
        except Exception as exc:  # noqa: BLE001 - operator CLI should print any actionable failure.
            last_error = exc
            print(f"[WARN] smoke attempt failed: {exc}")
            if attempt < max(1, args.retries):
                time.sleep(args.retry_delay)

    print(f"[FAIL] operator smoke failed: {last_error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
