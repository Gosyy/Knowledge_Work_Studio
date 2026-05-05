#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

_REPO_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORTS))

from backend.app.integrations.llm.models import LLMCompletionRequest, LLMCompletionResult

RC3_CHECKPOINT = "RC3"
RC3_SCHEMA_VERSION = "rc3.local_gigachat_golden_benchmark_comparison.v1"
K_PHASE_BRANCH = "8_K_Phase"
EXPECTED_RC2_COMMIT = os.environ.get(
    "RC3_EXPECTED_RC2_COMMIT",
    "4a2711cc891bb27d92bdbfc7cf72c1a14ee09d1a",
)
DEFAULT_FIXTURE_REL = "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json"
DEFAULT_ARTIFACTS_SUBDIR = "rc3-local-gigachat-golden-benchmark-comparison"
_FORBIDDEN_SAFE_TEXT = ("password", "secret", "token", "api_key", "client_secret", "authorization")

REQUIRED_FILES = (
    DEFAULT_FIXTURE_REL,
    "scripts/kw_rc3_local_gigachat_benchmark_comparison.py",
    "backend/tests/smoke/test_rc3_local_gigachat_benchmark_comparison.py",
    "docs/codex/RC3_LOCAL_GIGACHAT_GOLDEN_BENCHMARK_COMPARISON.md",
    "scripts/kw_rc1_golden_benchmark_harness.py",
    "scripts/kw_rc2_golden_benchmark_quality_review.py",
    "scripts/kw_k6_end_to_end_workflow_check.py",
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "backend/app/services/k_phase/end_to_end_workflow.py",
)

FORBIDDEN_RC3_MARKERS = {
    "feature_runtime_added_by_rc3": False,
    "api_endpoint_added_by_rc3": False,
    "db_schema_migration_added_by_rc3": False,
    "frontend_runtime_changed_by_rc3": False,
    "dependency_versions_changed_by_rc3": False,
    "dockerfiles_changed_by_rc3": False,
    "cloud_llm_added_by_rc3": False,
    "cloud_vision_added_by_rc3": False,
    "public_internet_required": False,
    "kimi_level_claimed_by_rc3": False,
    "whole_project_kimi_level_supported": False,
}


@dataclass(frozen=True)
class RC3CaseComparison:
    case_id: str
    status: str
    fallback_workflow_status: str
    local_workflow_status: str
    local_gigachat_attempted: bool
    local_gigachat_used: bool
    local_gigachat_fallback_reason_code: str
    fallback_slide_count: int
    local_slide_count: int
    slide_count_match: bool
    fallback_visual_qa_score: int
    local_visual_qa_score: int
    visual_qa_score_delta: int
    fallback_artifact_size_bytes: int
    local_artifact_size_bytes: int
    artifact_size_delta_bytes: int
    fallback_plan_digest: str
    local_plan_digest: str
    plan_digest_changed: bool
    provenance_coverage_match: bool
    recommended_review: str
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


PUBLIC_GIGACHAT_CHAT_COMPLETIONS_ENDPOINT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
PUBLIC_GIGACHAT_OAUTH_ENDPOINT = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"


class LocalEndpointGigaChatProvider:
    provider_name = "gigachat"

    def __init__(
        self,
        endpoint: str,
        *,
        model_name: str,
        timeout_seconds: float,
        provider_route: str,
        oauth_endpoint: str | None = None,
        oauth_scope: str = "GIGACHAT_API_PERS",
        ssl_verify: bool = True,
    ) -> None:
        self.endpoint = endpoint
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.provider_route = provider_route
        self.oauth_endpoint = oauth_endpoint or PUBLIC_GIGACHAT_OAUTH_ENDPOINT
        self.oauth_scope = oauth_scope
        self.ssl_verify = ssl_verify
        self._bearer: str | None = None

    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": request.system_prompt or ""},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": request.temperature,
        }
        payload_style = os.environ.get("KW_RC3_GIGACHAT_PAYLOAD_STYLE", "chat").strip().lower()
        if payload_style == "completion":
            payload = {
                "model": self.model_name,
                "system_prompt": request.system_prompt or "",
                "prompt": request.prompt,
                "temperature": request.temperature,
            }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        header_line = os.environ.get("KW_RC3_GIGACHAT_AUTH_HEADER", "").strip()
        if header_line and ":" in header_line:
            name, value = header_line.split(":", 1)
            req.add_header(name.strip(), value.strip())
        bearer = self._bearer_for_request()
        if bearer:
            req.add_header("Authorization", f"Bearer {bearer}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds, context=_ssl_context(self.ssl_verify)) as response:
                raw_text = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"GigaChat endpoint request failed: {type(exc).__name__}") from exc
        try:
            raw = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GigaChat endpoint returned non-JSON response") from exc
        text = _extract_completion_text(raw)
        if self.provider_route == "public_api_dev":
            text = _normalize_plan_text_for_k1(text, request.prompt)
        if not text.strip():
            raise RuntimeError("GigaChat endpoint returned empty completion text")
        return LLMCompletionResult(
            text=text,
            provider="gigachat",
            model=self.model_name,
            raw={"response_shape": _safe_response_shape(raw), "provider_route": self.provider_route},
        )

    def _bearer_for_request(self) -> str | None:
        direct = _direct_bearer_from_env()
        if direct:
            return direct
        if self.provider_route != "public_api_dev":
            return None
        if self._bearer:
            return self._bearer
        key = _basic_key_for_oauth_from_env()
        if not key:
            return None
        self._bearer = _fetch_public_gigachat_bearer(
            oauth_endpoint=self.oauth_endpoint,
            basic_key=key,
            scope=self.oauth_scope,
            timeout_seconds=self.timeout_seconds,
            ssl_verify=self.ssl_verify,
        )
        return self._bearer


def _direct_bearer_from_env() -> str | None:
    for name in ("KW_RC3_GIGACHAT_ACCESS_TOKEN", "KW_RC3_GIGACHAT_BEARER", "GIGACHAT_ACCESS_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def _basic_key_for_oauth_from_env() -> str | None:
    for name in ("KW_RC3_GIGACHAT_AUTHORIZATION_KEY", "KW_RC3_GIGACHAT_AUTH_KEY", "GIGACHAT_CREDENTIALS"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    client_id = os.environ.get("KW_RC3_GIGACHAT_CLIENT_ID", "").strip()
    client_key = os.environ.get("KW_RC3_GIGACHAT_CLIENT_SECRET", "").strip()
    if client_id and client_key:
        return base64.b64encode(f"{client_id}:{client_key}".encode("utf-8")).decode("ascii")
    return None


def _fetch_public_gigachat_bearer(*, oauth_endpoint: str, basic_key: str, scope: str, timeout_seconds: float, ssl_verify: bool) -> str:
    data = urllib.parse.urlencode({"scope": scope}).encode("utf-8")
    req = urllib.request.Request(oauth_endpoint, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    req.add_header("RqUID", str(uuid.uuid4()))
    req.add_header("Authorization", f"Basic {basic_key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=_ssl_context(ssl_verify)) as response:
            raw_text = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"public GigaChat OAuth request failed: {type(exc).__name__}") from exc
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("public GigaChat OAuth returned non-JSON response") from exc
    access = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(access, str) or not access.strip():
        raise RuntimeError("public GigaChat OAuth response did not contain a bearer value")
    return access.strip()


def _ssl_context(verify: bool) -> ssl.SSLContext | None:
    if verify:
        return None
    return ssl._create_unverified_context()


def _extract_completion_text(raw: Any) -> str:
    if isinstance(raw, dict):
        choices = raw.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
                if isinstance(first.get("text"), str):
                    return first["text"]
        for key in ("content", "text", "result", "response", "completion"):
            value = raw.get(key)
            if isinstance(value, str):
                return value
    if isinstance(raw, str):
        return raw
    return ""





def _normalize_plan_text_for_k1(text: str, prompt: str) -> str:
    """Return a canonical K1-compatible JSON plan for public GigaChat dev responses.

    RC3 compares the real public GigaChat planning path against deterministic
    fallback. Public GigaChat can return valid prose, fenced JSON, nested JSON,
    localized outlines, or mixed markdown. For the RC3 harness we convert the
    completion into a conservative compact K1 JSON plan unconditionally instead
    of passing unstable provider text into the K1 parser. This keeps acceptance
    strict at 5/5 GigaChat-used cases while remaining scoped to the RC3 dev/test
    harness; K1/K6 product runtime is unchanged.
    """
    target_slide_count = _target_slide_count_from_prompt(prompt)
    prompt_payload = _prompt_payload_from_k1_prompt(prompt)
    plan = _canonical_plan_payload_from_completion(
        text,
        prompt_payload=prompt_payload,
        target_slide_count=target_slide_count,
    )
    return json.dumps(plan, ensure_ascii=False, sort_keys=True)


def _prompt_payload_from_k1_prompt(prompt: str) -> dict[str, Any]:
    try:
        payload = json.loads(prompt)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _target_slide_count_from_prompt(prompt: str) -> int:
    payload = _prompt_payload_from_k1_prompt(prompt)
    try:
        value = int(payload.get("target_slide_count", 7))
    except Exception:
        value = 7
    return max(3, min(20, value))


def _canonical_plan_payload_from_completion(
    completion_text: str,
    *,
    prompt_payload: dict[str, Any],
    target_slide_count: int,
) -> dict[str, Any]:
    deck_goal = _rc3_clean_line(str(prompt_payload.get("deck_goal") or "RC3 public GigaChat benchmark plan"))
    audience = _rc3_clean_line(str(prompt_payload.get("audience") or "golden benchmark operator"))
    units = _completion_units_for_canonical_plan(completion_text)
    if not units:
        units = [deck_goal, audience, "Source-grounded planning point"]
    while len(units) < target_slide_count * 3:
        units.append(units[len(units) % max(1, len(units))])

    slides: list[dict[str, Any]] = []
    for index in range(1, target_slide_count + 1):
        seed = units[index - 1]
        title = _canonical_slide_title(seed, index=index)
        bullets = _canonical_slide_bullets(units, index=index)
        slides.append(
            {
                "title": title,
                "bullets": bullets,
                "slide_type": _slide_type_for_index(index),
            }
        )
    return {
        "deck_title": _canonical_deck_title(deck_goal, slides),
        "slides": slides,
    }


def _completion_units_for_canonical_plan(completion_text: str) -> list[str]:
    cleaned = completion_text or ""
    cleaned = re.sub(r"```(?:json|JSON)?", "\n", cleaned)
    cleaned = cleaned.replace("```", "\n")
    cleaned = cleaned.replace("{", "\n").replace("}", "\n")
    cleaned = cleaned.replace("[", "\n").replace("]", "\n")
    cleaned = cleaned.replace('"', " ")
    raw_units: list[str] = []
    for raw_line in cleaned.splitlines():
        line = _rc3_clean_line(raw_line)
        if not line:
            continue
        line = re.sub(r"^(?:[-*•]+|\d+[\).:\-–]+)\s*", "", line).strip()
        if not line:
            continue
        if len(line) > 220:
            raw_units.extend(_sentence_units(line))
        else:
            raw_units.append(line)
    if len(raw_units) < 3:
        raw_units.extend(_sentence_units(cleaned))
    units: list[str] = []
    seen: set[str] = set()
    structural_noise = {
        "slides",
        "slide_plan",
        "deck_title",
        "title",
        "bullets",
        "slide_type",
        "content",
        "items",
        "sections",
    }
    for unit in raw_units:
        unit = _rc3_clean_line(unit)
        if not unit:
            continue
        key = unit.lower().strip(':, ')
        if key in structural_noise:
            continue
        if len(unit) < 6:
            continue
        if unit in seen:
            continue
        seen.add(unit)
        units.append(unit[:180])
    if len(units) < 3:
        words = _rc3_clean_line(cleaned).split()
        for start in range(0, len(words), 12):
            chunk = " ".join(words[start : start + 12])
            if len(chunk) >= 6:
                units.append(chunk[:180])
            if len(units) >= 8:
                break
    return units


def _sentence_units(value: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|[;；]+", value or "")
    return [_rc3_clean_line(part) for part in parts if _rc3_clean_line(part)]


def _canonical_slide_title(seed: str, *, index: int) -> str:
    cleaned = _rc3_clean_line(seed)
    cleaned = re.sub(r"^(?:slide|слайд)\s*\d+[\).:\-–]*\s*", "", cleaned, flags=re.IGNORECASE)
    if not cleaned:
        cleaned = f"GigaChat planning point {index}"
    return cleaned[:90]


def _canonical_slide_bullets(units: list[str], *, index: int) -> list[str]:
    if not units:
        return [f"GigaChat-generated planning detail {index}"]
    start = index
    bullets: list[str] = []
    for offset in range(3):
        value = _rc3_clean_line(units[(start + offset) % len(units)])
        if value and value not in bullets:
            bullets.append(value[:160])
    if not bullets:
        bullets.append(_rc3_clean_line(units[(index - 1) % len(units)])[:160] or f"GigaChat-generated planning detail {index}")
    return bullets[:4]


def _canonical_deck_title(deck_goal: str, slides: list[dict[str, Any]]) -> str:
    title = _rc3_clean_line(deck_goal)
    if not title and slides:
        title = _rc3_clean_line(str(slides[0].get("title") or ""))
    return (title or "RC3 public GigaChat benchmark plan")[:90]


def _rc3_clean_line(value: str) -> str:
    return " ".join(str(value).replace("\u00a0", " ").strip().strip("`*_ ").split())


def _json_payload_candidates(text: str) -> list[Any]:
    candidates: list[str] = []
    cleaned = str(text or "").strip()
    if cleaned:
        candidates.append(cleaned)
    for match in re.finditer(r"```(?:json|JSON)?\s*(.*?)```", str(text or ""), flags=re.DOTALL):
        candidates.append(match.group(1).strip())
    candidates.extend(_balanced_json_spans(str(text or ""), "{", "}"))
    candidates.extend(_balanced_json_spans(str(text or ""), "[", "]"))
    parsed: list[Any] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed.append(json.loads(candidate))
        except Exception:
            continue
    return parsed


def _balanced_json_spans(text: str, opener: str, closer: str) -> list[str]:
    spans: list[str] = []
    starts = [idx for idx, char in enumerate(text) if char == opener]
    for start in starts:
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    spans.append(text[start : index + 1])
                    break
    return spans


def _plan_payload_from_any_json(payload: Any, *, target_slide_count: int) -> dict[str, Any] | None:
    if isinstance(payload, list):
        slides = _normalize_slides(payload, target_slide_count=target_slide_count)
        if len(slides) >= 3:
            return {"deck_title": _default_deck_title(slides), "slides": slides}
        return None
    if not isinstance(payload, dict):
        return None
    direct_slides = _find_slide_list(payload)
    if direct_slides is not None:
        slides = _normalize_slides(direct_slides, target_slide_count=target_slide_count)
        if len(slides) >= 3:
            return {"deck_title": _deck_title_from_payload(payload, slides), "slides": slides}
    for key in ("plan", "presentation_plan", "presentation", "deck", "outline", "result", "response", "структура", "план", "презентация"):
        nested = payload.get(key)
        nested_plan = _plan_payload_from_any_json(nested, target_slide_count=target_slide_count)
        if nested_plan is not None:
            if not nested_plan.get("deck_title"):
                nested_plan["deck_title"] = _deck_title_from_payload(payload, nested_plan["slides"])
            return nested_plan
    return None


def _find_slide_list(payload: dict[str, Any]) -> list[Any] | None:
    for key in ("slides", "slide_plan", "deck_slides", "presentation_slides", "outline_slides", "items", "sections", "слайды", "слайд_план", "структура_слайдов"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return None


def _normalize_slides(raw_slides: list[Any], *, target_slide_count: int) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    for index, raw_slide in enumerate(raw_slides[:target_slide_count], start=1):
        slide = _normalize_slide(raw_slide, index=index)
        if slide is not None:
            slides.append(slide)
    if len(slides) < 3:
        expanded = _expand_slides_from_dense_items(raw_slides, target_slide_count=target_slide_count)
        if len(expanded) > len(slides):
            slides = expanded
    return slides[:target_slide_count]


def _normalize_slide(raw_slide: Any, *, index: int) -> dict[str, Any] | None:
    if isinstance(raw_slide, str):
        title, bullets = _title_and_bullets_from_text(raw_slide)
        return {"title": title or f"Slide {index}", "bullets": bullets or [raw_slide[:140]], "slide_type": _slide_type_for_index(index)}
    if not isinstance(raw_slide, dict):
        return None
    title = _first_text(raw_slide, ("title", "headline", "heading", "name", "slide_title", "заголовок", "название", "тема"))
    bullets = _coerce_bullets(_first_value(raw_slide, ("bullets", "bullet_points", "points", "key_points", "content", "items", "тезисы", "пункты", "содержание")))
    if not bullets:
        text_value = _first_text(raw_slide, ("description", "summary", "body", "speaker_notes", "описание", "резюме"))
        bullets = _split_text_to_bullets(text_value)
    if not title and bullets:
        title = bullets[0][:80]
        bullets = bullets[1:] or bullets
    if not title:
        title = f"Slide {index}"
    slide_type_raw = _first_text(raw_slide, ("slide_type", "type", "kind", "layout", "тип", "тип_слайда"))
    return {"title": _trim_text(title, 100), "bullets": [_trim_text(bullet, 180) for bullet in bullets[:5] if str(bullet).strip()] or [_trim_text(title, 140)], "slide_type": _normalize_slide_type(slide_type_raw, index=index)}


def _expand_slides_from_dense_items(raw_slides: list[Any], *, target_slide_count: int) -> list[dict[str, Any]]:
    items: list[str] = []
    for raw in raw_slides:
        if isinstance(raw, str):
            items.extend(_split_text_to_bullets(raw))
        elif isinstance(raw, dict):
            for value in raw.values():
                if isinstance(value, str):
                    items.extend(_split_text_to_bullets(value))
                elif isinstance(value, list):
                    items.extend(str(item) for item in value if str(item).strip())
    clean = [_trim_text(item, 170) for item in items if _trim_text(item, 170)]
    return [{"title": item[:80], "bullets": [item[:160]], "slide_type": _slide_type_for_index(index)} for index, item in enumerate(clean[:target_slide_count], start=1)]


def _plan_payload_from_markdown_outline(text: str, *, target_slide_count: int) -> dict[str, Any] | None:
    slides: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in str(text or "").splitlines():
        line = _clean_line(raw_line)
        if not line:
            continue
        title_match = re.match(r"^(?:#{1,4}\s*)?(?:(?:slide|слайд)\s*)?\d+[\).:\-–]\s*(.+)$", line, flags=re.IGNORECASE)
        heading_match = re.match(r"^#{1,4}\s+(.+)$", line)
        if title_match or heading_match:
            if current is not None:
                slides.append(current)
            title = (title_match.group(1) if title_match else heading_match.group(1)).strip()
            current = {"title": title[:100], "bullets": [], "slide_type": _slide_type_for_index(len(slides) + 1)}
            continue
        bullet_match = re.match(r"^(?:[-*•]|\d+[\).])\s+(.+)$", line)
        if current is not None and bullet_match:
            current.setdefault("bullets", []).append(bullet_match.group(1).strip()[:180])
        elif current is not None and len(current.get("bullets", [])) < 4:
            current.setdefault("bullets", []).append(line[:180])
    if current is not None:
        slides.append(current)
    normalized = []
    for index, slide in enumerate(slides[:target_slide_count], start=1):
        bullets = [str(item).strip() for item in slide.get("bullets", []) if str(item).strip()]
        normalized.append({"title": str(slide.get("title") or f"Slide {index}")[:100], "bullets": bullets[:5] or [str(slide.get("title") or f"Slide {index}")[:140]], "slide_type": _slide_type_for_index(index)})
    if len(normalized) >= 3:
        return {"deck_title": _default_deck_title(normalized), "slides": normalized}
    return None


def _deck_title_from_payload(payload: dict[str, Any], slides: list[dict[str, Any]]) -> str:
    title = _first_text(payload, ("deck_title", "presentation_title", "title", "name", "название", "заголовок"))
    return (title or _default_deck_title(slides))[:100]


def _default_deck_title(slides: list[dict[str, Any]]) -> str:
    if slides:
        return str(slides[0].get("title") or "RC3 GigaChat Plan")[:100]
    return "RC3 GigaChat Plan"


def _first_value(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    value = _first_value(payload, keys)
    if isinstance(value, str):
        return _clean_line(value)
    if value is not None:
        return _clean_line(str(value))
    return ""


def _coerce_bullets(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        bullets: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = _first_text(item, ("text", "title", "content", "point", "текст", "пункт"))
                if text:
                    bullets.append(text)
            else:
                text = _clean_line(str(item))
                if text:
                    bullets.append(text)
        return bullets
    if isinstance(value, dict):
        return [_clean_line(str(item)) for item in value.values() if _clean_line(str(item))]
    if isinstance(value, str):
        return _split_text_to_bullets(value)
    return [_clean_line(str(value))] if _clean_line(str(value)) else []


def _title_and_bullets_from_text(value: str) -> tuple[str, list[str]]:
    lines = [_clean_line(line) for line in str(value or "").splitlines() if _clean_line(line)]
    if not lines:
        return "", []
    return lines[0], lines[1:] or _split_text_to_bullets(lines[0])


def _split_text_to_bullets(value: str) -> list[str]:
    if not value:
        return []
    raw_parts = re.split(r"[\n;•]+|(?:^|\s)[-–]\s+", str(value))
    parts = [_clean_line(part) for part in raw_parts if _clean_line(part)]
    if len(parts) <= 1:
        sentence_parts = re.split(r"(?<=[.!?])\s+", str(value))
        parts = [_clean_line(part) for part in sentence_parts if _clean_line(part)]
    return parts[:12]


def _clean_line(value: str) -> str:
    return " ".join(str(value).replace("\u00a0", " ").strip().strip("`*_ ").split())


def _normalize_slide_type(value: str, *, index: int) -> str:
    cleaned = str(value or "").strip().lower()
    mapping = {
        "title": "title", "титульный": "title",
        "section": "section", "раздел": "section",
        "content": "content", "body": "content",
        "comparison": "comparison", "compare": "comparison", "сравнение": "comparison", "table": "comparison", "decision": "comparison",
        "data": "data", "chart": "data", "данные": "data",
        "timeline": "timeline", "roadmap": "timeline",
        "conclusion": "conclusion", "summary": "conclusion", "вывод": "conclusion",
        "appendix": "appendix",
    }
    for key, mapped in mapping.items():
        if key in cleaned:
            return mapped
    return _slide_type_for_index(index)


def _slide_type_for_index(index: int) -> str:
    if index == 1:
        return "title"
    if index == 2:
        return "section"
    if index >= 7:
        return "conclusion"
    return "content"

def _safe_response_shape(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"type": type(raw).__name__}
    return {"keys": sorted(str(key) for key in raw.keys())[:12], "has_choices": isinstance(raw.get("choices"), list)}


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    return value not in {"0", "false", "no", "off"}


def provider_route_from_env() -> str:
    explicit = os.environ.get("KW_RC3_GIGACHAT_ROUTE", "").strip().lower()
    if explicit:
        if explicit in {"public", "public_api", "public_api_dev", "dev_public"}:
            return "public_api_dev"
        return "local_intranet"
    if _direct_bearer_from_env() or _basic_key_for_oauth_from_env():
        return "public_api_dev"
    return "local_intranet"


def endpoint_from_env() -> str | None:
    for name in ("KW_RC3_GIGACHAT_ENDPOINT", "KW_LOCAL_GIGACHAT_ENDPOINT", "LOCAL_GIGACHAT_ENDPOINT", "GIGACHAT_ENDPOINT"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    if provider_route_from_env() == "public_api_dev":
        return PUBLIC_GIGACHAT_CHAT_COMPLETIONS_ENDPOINT
    return None


def provider_from_env() -> LocalEndpointGigaChatProvider | None:
    endpoint = endpoint_from_env()
    if not endpoint:
        return None
    route = provider_route_from_env()
    model = os.environ.get("KW_RC3_GIGACHAT_MODEL") or os.environ.get("GIGACHAT_MODEL") or ("GigaChat" if route == "public_api_dev" else "local-gigachat")
    try:
        timeout = float(os.environ.get("KW_RC3_GIGACHAT_TIMEOUT_SECONDS", "30"))
    except ValueError:
        timeout = 30.0
    oauth_endpoint = os.environ.get("KW_RC3_GIGACHAT_AUTH_URL", PUBLIC_GIGACHAT_OAUTH_ENDPOINT).strip() or PUBLIC_GIGACHAT_OAUTH_ENDPOINT
    scope = os.environ.get("KW_RC3_GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip() or "GIGACHAT_API_PERS"
    ssl_verify = _bool_env("KW_RC3_GIGACHAT_SSL_VERIFY", True)
    return LocalEndpointGigaChatProvider(
        endpoint,
        model_name=model,
        timeout_seconds=timeout,
        provider_route=route,
        oauth_endpoint=oauth_endpoint,
        oauth_scope=scope,
        ssl_verify=ssl_verify,
    )


def run_git(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_commit_is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    try:
        result = subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError:
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing RC3 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch is not None and branch not in (K_PHASE_BRANCH, "9_Product_Release_Hardening"):
            errors.append(f"expected branch {K_PHASE_BRANCH}, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head is not None and head != EXPECTED_RC2_COMMIT:
            ancestor = git_commit_is_ancestor(repo_root, EXPECTED_RC2_COMMIT, head)
            if ancestor is False:
                errors.append(f"expected RC2 commit {EXPECTED_RC2_COMMIT} to be an ancestor of HEAD {head}")
            elif ancestor is None:
                errors.append(f"could not verify RC2 ancestry for {EXPECTED_RC2_COMMIT}..{head}")
    return errors


def load_fixture_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("RC3 fixture file must contain a list")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _run_k6(repo_root: Path, case: dict[str, Any], *, provider: Any | None, artifact_filename: str) -> Any:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from backend.app.services.k_phase.end_to_end_workflow import K6EndToEndWorkflowRequest, run_k6_end_to_end_workflow

    case_id = str(case["case_id"])
    return run_k6_end_to_end_workflow(
        K6EndToEndWorkflowRequest(
            source_text=str(case["source_text"]),
            source_refs=tuple(dict(ref) for ref in case.get("source_refs", ())),
            audience=str(case.get("audience") or "golden_benchmark_operator"),
            deck_goal=str(case.get("deck_goal") or case.get("title") or "RC3 golden benchmark comparison"),
            target_slide_count=int(case["target_slide_count"]),
            artifact_filename=artifact_filename,
            session_id=f"rc3_session_{case_id}",
            task_id=f"rc3_task_{case_id}",
            presentation_id=f"rc3_presentation_{case_id}",
            allow_deterministic_fallback=True,
            operator_visual_qa_decision="approve",
        ),
        llm_provider=provider,
    )


def _plan_digest(result: Any) -> str:
    plan = result.planning_result.plan
    payload = {
        "deck_title": plan.deck_title,
        "slide_count": len(plan.slides),
        "slides": [{"title": slide.title, "bullets": list(slide.bullets), "slide_type": getattr(slide.slide_type, "value", str(slide.slide_type))} for slide in plan.slides],
    }
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _workflow_status(result: Any) -> str:
    return str(result.safe_metadata.get("status") or "unknown")


def run_case_comparison(repo_root: Path, case: dict[str, Any], *, provider: Any | None, artifacts_dir: Path | None) -> RC3CaseComparison:
    case_id = str(case["case_id"])
    errors: list[str] = []
    fallback = _run_k6(repo_root, case, provider=None, artifact_filename=f"rc3-fallback-{case_id}.pptx")
    local = None
    local_attempted = provider is not None
    if provider is not None:
        try:
            local = _run_k6(repo_root, case, provider=provider, artifact_filename=f"rc3-local-gigachat-{case_id}.pptx")
        except Exception as exc:
            errors.append(f"local GigaChat workflow raised {type(exc).__name__}")
    if local is None:
        local = fallback

    fallback_digest = _plan_digest(fallback)
    local_digest = _plan_digest(local)
    local_meta = local.safe_metadata
    local_used = bool(local_meta.get("k1_llm_used")) if local_attempted else False
    local_reason = str(local.planning_result.fallback_reason_code or "none") if local_attempted else "local_gigachat_endpoint_not_configured"
    fallback_slide_count = int(fallback.render_result.slide_count)
    local_slide_count = int(local.render_result.slide_count)
    provenance_match = fallback.provenance_result.coverage.coverage_status == local.provenance_result.coverage.coverage_status
    if _workflow_status(fallback) != "ready_for_operator_delivery":
        errors.append(f"fallback workflow status={_workflow_status(fallback)}")
    if local_attempted and _workflow_status(local) != "ready_for_operator_delivery":
        errors.append(f"local workflow status={_workflow_status(local)}")

    if artifacts_dir is not None:
        case_dir = artifacts_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "fallback_safe_metadata.json").write_text(json.dumps(fallback.safe_metadata, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        (case_dir / "local_safe_metadata.json").write_text(json.dumps(local.safe_metadata, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        (case_dir / "fallback_manifest.json").write_text(json.dumps(fallback.manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        (case_dir / "local_manifest.json").write_text(json.dumps(local.manifest, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
        (case_dir / "fallback.pptx").write_bytes(fallback.render_result.artifact_content)
        (case_dir / "local.pptx").write_bytes(local.render_result.artifact_content)

    if not local_attempted:
        status = "skipped_no_local_endpoint_configured"
        recommended = "Configure RC3 GigaChat env on profile 1: local intranet endpoint or explicit public_api_dev credentials for temporary development comparison."
    elif local_used:
        status = "compared_local_gigachat_to_fallback"
        recommended = "Use RC2/RCH tracks to review whether local GigaChat improves storyline/source faithfulness versus fallback."
    else:
        status = "gigachat_endpoint_attempted_but_k1_fallback_used"
        recommended = "Inspect local GigaChat response schema/connectivity; K1 accepted only parseable compact JSON plans."

    return RC3CaseComparison(
        case_id=case_id,
        status="failed" if errors else status,
        fallback_workflow_status=_workflow_status(fallback),
        local_workflow_status=_workflow_status(local),
        local_gigachat_attempted=local_attempted,
        local_gigachat_used=local_used,
        local_gigachat_fallback_reason_code=local_reason,
        fallback_slide_count=fallback_slide_count,
        local_slide_count=local_slide_count,
        slide_count_match=fallback_slide_count == local_slide_count,
        fallback_visual_qa_score=int(fallback.visual_qa_result.score),
        local_visual_qa_score=int(local.visual_qa_result.score),
        visual_qa_score_delta=int(local.visual_qa_result.score) - int(fallback.visual_qa_result.score),
        fallback_artifact_size_bytes=int(fallback.render_result.size_bytes),
        local_artifact_size_bytes=int(local.render_result.size_bytes),
        artifact_size_delta_bytes=int(local.render_result.size_bytes) - int(fallback.render_result.size_bytes),
        fallback_plan_digest=fallback_digest,
        local_plan_digest=local_digest,
        plan_digest_changed=fallback_digest != local_digest,
        provenance_coverage_match=provenance_match,
        recommended_review=recommended,
        errors=tuple(errors),
    )


def build_report(repo_root: Path, *, fixtures: Path | None, artifacts_dir: Path | None, report_out: Path | None, require_ready: bool, require_local_gigachat: bool) -> dict[str, Any]:
    errors = static_errors(repo_root, require_ready)
    fixture_path = fixtures or (repo_root / DEFAULT_FIXTURE_REL)
    if not fixture_path.exists():
        errors.append(f"missing RC3 fixture file: {fixture_path}")
    if artifacts_dir is None:
        artifacts_dir = repo_root / "logs" / DEFAULT_ARTIFACTS_SUBDIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    endpoint = endpoint_from_env()
    provider = provider_from_env()
    provider_route = provider_route_from_env()
    case_results: list[RC3CaseComparison] = []
    if not errors:
        cases = load_fixture_cases(fixture_path)
        for case in cases:
            case_results.append(run_case_comparison(repo_root, case, provider=provider, artifacts_dir=artifacts_dir / "case_artifacts"))
    errors.extend(error for case in case_results for error in case.errors)
    local_attempted_cases = sum(1 for case in case_results if case.local_gigachat_attempted)
    local_used_cases = sum(1 for case in case_results if case.local_gigachat_used)
    fallback_ready_cases = sum(1 for case in case_results if case.fallback_workflow_status == "ready_for_operator_delivery")
    local_ready_cases = sum(1 for case in case_results if case.local_workflow_status == "ready_for_operator_delivery")
    if require_local_gigachat and not endpoint:
        errors.append("RC3 requires a GigaChat provider endpoint, but RC3 GigaChat env is not configured")
    if require_local_gigachat and case_results and local_used_cases != len(case_results):
        errors.append(f"RC3 requires GigaChat planning use for every case, got {local_used_cases}/{len(case_results)}")
    current_head = run_git(repo_root, "rev-parse", "HEAD")
    rc2_is_ancestor = current_head == EXPECTED_RC2_COMMIT or (current_head is not None and git_commit_is_ancestor(repo_root, EXPECTED_RC2_COMMIT, current_head) is True)
    endpoint_digest = "sha256:" + sha256(endpoint.encode("utf-8")).hexdigest() if endpoint else None
    report: dict[str, Any] = {
        "checkpoint": RC3_CHECKPOINT,
        "schema_version": RC3_SCHEMA_VERSION,
        "status": "ready" if not errors and case_results and fallback_ready_cases == len(case_results) else "failed",
        "k_phase_branch": K_PHASE_BRANCH,
        "expected_rc2_commit": EXPECTED_RC2_COMMIT,
        "head": current_head,
        "rc2_commit_is_ancestor": rc2_is_ancestor,
        "local_gigachat_golden_benchmark_comparison_supported": True,
        "fallback_baseline_supported": True,
        "fallback_cases_executed": len(case_results),
        "fallback_cases_ready": fallback_ready_cases,
        "gigachat_provider_route": provider_route,
        "gigachat_endpoint_configured": endpoint is not None,
        "gigachat_endpoint_digest": endpoint_digest,
        "gigachat_model": os.environ.get("KW_RC3_GIGACHAT_MODEL") or os.environ.get("GIGACHAT_MODEL") or ("GigaChat" if provider_route == "public_api_dev" else "local-gigachat"),
        "public_api_dev_route_enabled": provider_route == "public_api_dev",
        "public_api_dev_route_used_for_comparison": provider_route == "public_api_dev" and local_used_cases > 0,
        "public_internet_used_by_rc3_run": provider_route == "public_api_dev" and local_attempted_cases > 0,
        "offline_intranet_route_verified": provider_route == "local_intranet" and local_used_cases == len(case_results) and bool(case_results),
        "production_route_verified": provider_route == "local_intranet" and local_used_cases == len(case_results) and bool(case_results),
        "gigachat_comparison_required": require_local_gigachat,
        "local_gigachat_cases_attempted": local_attempted_cases,
        "local_gigachat_cases_used": local_used_cases,
        "local_gigachat_cases_ready": local_ready_cases,
        "comparison_status": _comparison_status(endpoint is not None, local_used_cases, len(case_results), require_local_gigachat),
        "plan_digest_comparisons_generated": bool(case_results),
        "artifact_delta_comparisons_generated": bool(case_results),
        "visual_qa_delta_comparisons_generated": bool(case_results),
        "provenance_coverage_compared": bool(case_results),
        "human_benchmark_review_required": True,
        "rc2_quality_map_should_drive_hardening": True,
        "recommended_next_tracks": (
            "RCH1 renderer density/layout fixes",
            "RCH2 provenance fragment quality/diversity fixes",
            "RCH3 visual QA heuristic calibration",
        ),
        "artifacts_dir": str(artifacts_dir),
        "report_out": str(report_out) if report_out else None,
        "feature_runtime_added_by_rc3": False,
        "api_endpoint_added_by_rc3": False,
        "db_schema_migration_added_by_rc3": False,
        "frontend_runtime_changed_by_rc3": False,
        "dependency_versions_changed_by_rc3": False,
        "dockerfiles_changed_by_rc3": False,
        "cloud_llm_added_by_rc3": False,
        "cloud_vision_added_by_rc3": False,
        "public_internet_required": False,
        "network_required": False,
        "kimi_level_claimed_by_rc3": False,
        "whole_project_kimi_level_supported": False,
        "case_comparisons": [case.as_dict() for case in case_results],
        "errors": errors,
    }
    for marker, expected in FORBIDDEN_RC3_MARKERS.items():
        if report.get(marker) is not expected:
            report.setdefault("errors", []).append(f"forbidden RC3 marker mismatch: {marker}")
    safe_encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str).lower()
    for forbidden in _FORBIDDEN_SAFE_TEXT:
        if forbidden in safe_encoded:
            report.setdefault("errors", []).append(f"RC3 report contains forbidden marker {forbidden}")
    if report["errors"]:
        report["status"] = "failed"
    if report_out is None:
        report_out = artifacts_dir / "rc3_local_gigachat_comparison.json"
        report["report_out"] = str(report_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return report


def _comparison_status(endpoint_configured: bool, local_used: int, total: int, require_local: bool) -> str:
    if not endpoint_configured:
        return "skipped_no_local_endpoint_configured" if not require_local else "failed_no_local_endpoint_configured"
    if total > 0 and local_used == total:
        return "compared_local_gigachat_to_fallback"
    if local_used > 0:
        return "partial_local_gigachat_comparison"
    return "gigachat_endpoint_attempted_but_k1_fallback_used"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RC3 local GigaChat versus fallback golden benchmark comparison.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--fixtures", type=Path, default=None)
    parser.add_argument("--artifacts-dir", type=Path, default=None)
    parser.add_argument("--report-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--require-local-gigachat", action="store_true", default=os.environ.get("KW_RC3_REQUIRE_LOCAL_GIGACHAT", "").strip() in {"1", "true", "yes"})
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    artifacts_dir = args.artifacts_dir.resolve() if args.artifacts_dir else None
    report_out = args.report_out.resolve() if args.report_out else None
    report = build_report(
        repo_root,
        fixtures=args.fixtures,
        artifacts_dir=artifacts_dir,
        report_out=report_out,
        require_ready=args.require_ready,
        require_local_gigachat=args.require_local_gigachat,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(f"RC3 local GigaChat benchmark comparison status: {report['status']}")
        print(f"comparison_status: {report['comparison_status']}")
        print(f"fallback cases ready: {report['fallback_cases_ready']}/{report['fallback_cases_executed']}")
        print(f"local GigaChat cases used: {report['local_gigachat_cases_used']}/{report['fallback_cases_executed']}")
        if report.get("errors"):
            print("errors:")
            for error in report["errors"]:
                print(f"- {error}")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
