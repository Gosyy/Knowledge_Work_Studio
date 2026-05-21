from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

from backend.app.services.slides_service.canonical_schema_adapter import (
    adapt_minimal_model_payload_to_canonical,
    validate_canonical_s13g_payload,
)
from backend.app.services.slides_service.kimi_style_benchmark import S10_SCENARIO_IDS
from backend.app.services.slides_service.live_gigachat_selected_benchmark import PUBLIC_API_DEV_ROUTE, REQUIRED_PROVIDER
from backend.app.services.slides_service.single_scenario_s13h_retry import (
    S13I_EXPECTED_FINAL_CANONICAL_VALID_COUNT,
    S13I_EXPECTED_PRIOR_CANONICAL_VALID_COUNT,
    S13I_RETRY_SCENARIO_ID,
    single_scenario_executive_memo_retry_report,
)
from backend.app.services.slides_service.strict_json_per_scenario_rerun import MIN_REQUIRED_SLIDES_PER_SCENARIO

S13J_WORKFLOW_ID = "slides.executive_memo_deterministic_salvage"
S13J_PHASE_ID = "S13j"
S13J_SCHEMA_VERSION = "s13j.executive_memo_salvage.v1"
S13J_EXPECTED_PRIOR_CANONICAL_VALID_COUNT = S13I_EXPECTED_PRIOR_CANONICAL_VALID_COUNT
S13J_EXPECTED_FINAL_CANONICAL_VALID_COUNT = S13I_EXPECTED_FINAL_CANONICAL_VALID_COUNT

S13J_SALVAGE_ACTIONS = (
    "strip_markdown_fences_if_present",
    "sanitize_invalid_control_characters",
    "json_loads_original_or_sanitized_candidate",
    "raw_decode_first_json_value",
    "safe_comma_insertion_between_adjacent_fields",
    "bracket_balancing_for_truncated_object",
    "truncate_to_largest_parseable_json_object_if_safe",
    "fallback_text_to_minimal_model_adapter_only_after_json_salvage_failure",
    "preserve_original_response_digest",
    "write_s13j_salvage_manifest",
    "mark_salvage_generated_fields_as_not_model_generated",
)

FORBIDDEN_S13J_ACTIONS = (
    "call_gigachat_again",
    "retry_any_scenario_with_llm",
    "discard_11_s13i_canonical_valid_outputs",
    "treat_salvage_fields_as_model_generated",
    "fabricate_human_review_results",
    "auto_approve_scenarios",
    "claim_selected_offline_workflow_parity",
    "claim_kimi_level_achieved",
    "claim_server3_local_intranet_verified",
    "record_raw_credentials",
)

FIELD_NAMES_FOR_SAFE_COMMA_INSERTION = (
    "scenario_id",
    "deck_title",
    "title",
    "storyline",
    "slides",
    "slide_outline",
    "purpose",
    "objective",
    "key_claims",
    "claims",
    "content",
    "visual_intent",
    "visual",
    "native_visuals",
    "citation_needs",
    "citation_requirements",
    "risks_or_open_questions",
    "scenario_summary",
    "summary",
)


@dataclass(frozen=True)
class ExecutiveMemoSalvagePolicy:
    scenario_id: str
    route: str
    provider: str
    salvage_required: bool
    reuse_prior_s13i_output: bool
    salvage_reason: str
    calls_gigachat: bool = False
    completed_human_review_results_present: bool = False
    selected_parity_claim_supported_now: bool = False
    server3_local_intranet_verified: bool = False
    kimi_level_claimed: bool = False
    credential_values_recorded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SalvageParseResult:
    payload: Any | None
    actions: tuple[str, ...]
    method: str
    parse_error: str | None
    used_text_to_minimal_model_adapter: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_executive_memo_salvage_policies() -> tuple[ExecutiveMemoSalvagePolicy, ...]:
    policies: list[ExecutiveMemoSalvagePolicy] = []
    for scenario_id in S10_SCENARIO_IDS:
        salvage_required = scenario_id == S13I_RETRY_SCENARIO_ID
        policies.append(
            ExecutiveMemoSalvagePolicy(
                scenario_id=scenario_id,
                route=PUBLIC_API_DEV_ROUTE,
                provider=REQUIRED_PROVIDER,
                salvage_required=salvage_required,
                reuse_prior_s13i_output=not salvage_required,
                salvage_reason="s13i_executive_memo_json_parse_failed" if salvage_required else "canonical_valid_in_prior_s13i",
            )
        )
    return tuple(policies)


S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES = build_executive_memo_salvage_policies()


def json_digest(payload: object) -> str:
    return "sha256:" + sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8", errors="replace")).hexdigest()


def strip_markdown_fences(text: str) -> tuple[str, bool]:
    candidate = text.strip()
    if not candidate.startswith("```"):
        return candidate, False
    candidate = re.sub(r"^```(?:json|JSON)?\s*", "", candidate)
    candidate = re.sub(r"\s*```\s*$", "", candidate)
    return candidate.strip(), True


def sanitize_invalid_control_characters(text: str) -> tuple[str, bool]:
    sanitized = "".join(" " if ord(ch) < 32 and ch not in "\t\r\n" else ch for ch in text)
    return sanitized, sanitized != text


def _try_json(candidate: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(candidate), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def _try_raw_decode(candidate: str) -> tuple[Any | None, bool, str | None]:
    try:
        payload, end = json.JSONDecoder().raw_decode(candidate.strip())
        return payload, bool(candidate.strip()[end:].strip()), None
    except json.JSONDecodeError as exc:
        return None, False, str(exc)


def insert_safe_commas_between_adjacent_fields(text: str) -> tuple[str, bool]:
    field_pattern = "|".join(re.escape(name) for name in FIELD_NAMES_FOR_SAFE_COMMA_INSERTION)
    patterns = (
        (rf'([\}}\]\"])(\s+)("(?:{field_pattern})"\s*:)', r"\1,\2\3"),
        (rf'(\d|true|false|null)(\s+)("(?:{field_pattern})"\s*:)', r"\1,\2\3"),
    )
    candidate = text
    for pattern, replacement in patterns:
        candidate = re.sub(pattern, replacement, candidate)
    return candidate, candidate != text


def balance_brackets(text: str) -> tuple[str, bool]:
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "[{":
            stack.append("}" if ch == "{" else "]")
        elif ch in "]}":
            if stack and stack[-1] == ch:
                stack.pop()
            else:
                return text, False
    if in_string:
        text += '"'
    if stack:
        return text + "".join(reversed(stack)), True
    return text, in_string


def _json_object_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    stack: list[str] = []
    start: int | None = None
    in_string = False
    escape = False
    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if not stack:
                start = idx
            stack.append("}")
        elif ch == "[":
            if stack:
                stack.append("]")
        elif ch in "}]" and stack:
            expected = stack.pop()
            if ch != expected:
                stack.clear()
                start = None
                continue
            if not stack and start is not None:
                ranges.append((start, idx + 1))
                start = None
    return ranges


def largest_parseable_json_object(text: str) -> tuple[Any | None, bool, str | None]:
    last_error: str | None = None
    for start, end in sorted(_json_object_ranges(text), key=lambda pair: pair[1] - pair[0], reverse=True):
        payload, error = _try_json(text[start:end])
        if error is None:
            return payload, start != 0 or end != len(text.strip()), None
        last_error = error
    return None, False, last_error or "no balanced JSON object found"


def deterministic_text_to_minimal_payload(text: str, scenario_id: str) -> dict[str, Any]:
    compact = re.sub(r"\s+", " ", text).strip()
    snippets = [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]
    if not snippets:
        snippets = [f"Malformed S13i response for {scenario_id} requires human review."]
    storyline = (snippets + [
        "Deterministic salvage preserved the response digest for reviewer audit.",
        "Human review remains pending and must not be auto-filled.",
        "No selected parity, Kimi-level, or Server 3 local_intranet claim is supported.",
    ])[:4]
    slides: list[dict[str, Any]] = []
    for index in range(1, MIN_REQUIRED_SLIDES_PER_SCENARIO + 1):
        source_snippet = snippets[(index - 1) % len(snippets)][:180]
        slides.append(
            {
                "title": f"Executive memo salvage slide {index}",
                "purpose": f"Deterministic fallback slide {index} for {scenario_id}; reviewer must verify source grounding.",
                "key_claims": [source_snippet or f"{scenario_id} claim requires source grounding"],
                "visual_intent": "text_box" if index % 2 else "pptx_table",
                "citation_needs": ["claim_to_source_fragment_mapping_required"],
            }
        )
    return {
        "scenario_id": scenario_id,
        "deck_title": "Executive memo to board deck salvage candidate",
        "storyline": storyline,
        "slides": slides,
        "risks_or_open_questions": [
            "JSON salvage fallback used deterministic text-to-minimal-model adapter.",
            "All fallback fields are salvage-generated and are not model-generated.",
            "Human reviewer must verify claims before any release decision.",
        ],
        "salvage_generated_fields": ["deck_title", "storyline", "slides", "risks_or_open_questions"],
    }


def salvage_jsonish_minimal_payload(text: str, scenario_id: str, *, allow_text_adapter: bool = True) -> SalvageParseResult:
    actions: list[str] = []
    candidate, stripped = strip_markdown_fences(text)
    if stripped:
        actions.append("strip_markdown_fences")
    candidate, sanitized = sanitize_invalid_control_characters(candidate)
    if sanitized:
        actions.append("sanitize_invalid_control_characters")

    attempts: list[tuple[str, str]] = [("json_loads_sanitized_candidate", candidate)]
    comma_candidate, commas_inserted = insert_safe_commas_between_adjacent_fields(candidate)
    if commas_inserted:
        actions.append("safe_comma_insertion_between_adjacent_fields")
        attempts.append(("json_loads_after_safe_comma_insertion", comma_candidate))
    balanced_candidate, balanced = balance_brackets(comma_candidate)
    if balanced:
        actions.append("bracket_balancing_for_truncated_object")
        attempts.append(("json_loads_after_bracket_balancing", balanced_candidate))

    last_error: str | None = None
    for method, attempt in attempts:
        payload, error = _try_json(attempt)
        if error is None:
            return SalvageParseResult(payload, tuple(actions + [method]), method, None, False)
        last_error = error
        payload, trailing, raw_error = _try_raw_decode(attempt)
        if raw_error is None:
            raw_actions = actions + ["raw_decode_first_json_value"]
            if trailing:
                raw_actions.append("trim_trailing_extra_data")
            return SalvageParseResult(payload, tuple(raw_actions), "raw_decode_first_json_value", None, False)
        last_error = raw_error

    payload, truncated, error = largest_parseable_json_object(balanced_candidate)
    if error is None:
        object_actions = actions + ["truncate_to_largest_parseable_json_object"]
        if truncated:
            object_actions.append("largest_balanced_object_selected")
        return SalvageParseResult(payload, tuple(object_actions), "largest_parseable_json_object", None, False)
    last_error = error

    if allow_text_adapter:
        fallback = deterministic_text_to_minimal_payload(text, scenario_id)
        return SalvageParseResult(
            fallback,
            tuple(actions + ["fallback_text_to_minimal_model_adapter"]),
            "fallback_text_to_minimal_model_adapter",
            last_error,
            True,
        )
    return SalvageParseResult(None, tuple(actions), "json_salvage_failed", last_error, False)


def extract_response_text_from_s13i_payload(payload: dict[str, Any]) -> str:
    for key in ("response_text", "raw_response_text", "model_response_text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    response = payload.get("response")
    if isinstance(response, dict):
        try:
            content = response["choices"][0]["message"]["content"]
            if isinstance(content, str):
                return content
        except Exception:
            return ""
    return ""


def adapt_salvaged_payload_to_canonical(
    payload: Any,
    scenario_id: str,
    *,
    source_response_digest: str,
    raw_response_text_digest: str,
    salvage_result: SalvageParseResult,
) -> dict[str, Any]:
    canonical = adapt_minimal_model_payload_to_canonical(payload, scenario_id)
    provenance = canonical.setdefault("adapter_provenance", {})
    if salvage_result.used_text_to_minimal_model_adapter:
        provenance["model_provided_fields"] = []
        adapter_added = set(provenance.get("adapter_added_fields") or [])
        adapter_added.update({"salvage_fallback_minimal_payload", "salvage_generated_fields"})
        provenance["adapter_added_fields"] = sorted(str(item) for item in adapter_added)
    provenance["s13j_salvage_schema_version"] = S13J_SCHEMA_VERSION
    provenance["s13j_salvage_method"] = salvage_result.method
    provenance["s13j_salvage_actions"] = list(salvage_result.actions)
    provenance["source_s13i_response_digest"] = source_response_digest
    provenance["raw_response_text_digest"] = raw_response_text_digest
    provenance["salvage_generated_fields_are_not_model_generated"] = True
    provenance["adapter_fields_are_not_model_generated"] = True
    normalization = set(provenance.get("normalization_actions") or [])
    normalization.update(salvage_result.actions)
    normalization.add("s13j_preserve_original_response_digest")
    normalization.add("s13j_mark_salvage_fields_not_model_generated")
    provenance["normalization_actions"] = sorted(str(item) for item in normalization)
    safety = canonical.setdefault("safety_boundaries", {})
    safety["selected_parity_claim_supported_now"] = False
    safety["kimi_level_claimed"] = False
    safety["server3_local_intranet_verified"] = False
    safety["completed_human_review_results_present"] = False
    safety["credential_values_recorded"] = False
    canonical["human_review_handoff"] = {
        "review_state": "pending_human_review",
        "allowed_decisions": ["approve", "request_rework", "reject"],
        "do_not_auto_fill": True,
    }
    return canonical


def validate_executive_memo_salvage_contract() -> list[str]:
    errors: list[str] = []
    s13i = single_scenario_executive_memo_retry_report()
    if s13i.get("status") != "ready":
        errors.append("S13j requires S13i single-scenario retry contract to be ready")
    if len(S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES) != len(S10_SCENARIO_IDS):
        errors.append("S13j must cover all 12 selected benchmark scenarios")
    salvage_policies = [policy for policy in S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES if policy.salvage_required]
    reused_policies = [policy for policy in S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES if policy.reuse_prior_s13i_output]
    if [policy.scenario_id for policy in salvage_policies] != [S13I_RETRY_SCENARIO_ID]:
        errors.append("S13j must salvage only executive_memo_to_board_deck")
    if len(reused_policies) != S13J_EXPECTED_PRIOR_CANONICAL_VALID_COUNT:
        errors.append("S13j must reuse 11 prior S13i canonical-valid outputs")

    malformed = '{"scenario_id":"executive_memo_to_board_deck" "deck_title":"Board memo" "storyline":["context","analysis","decision","actions"],"slides":[{"title":"One","purpose":"Purpose","key_claims":["claim"],"visual_intent":"text_box","citation_needs":["source"]}]}'
    result = salvage_jsonish_minimal_payload(malformed, S13I_RETRY_SCENARIO_ID)
    if result.payload is None:
        errors.append("S13j sample malformed payload did not produce a salvage payload")
    else:
        canonical = adapt_salvaged_payload_to_canonical(
            result.payload,
            S13I_RETRY_SCENARIO_ID,
            source_response_digest=json_digest({"sample": "response"}),
            raw_response_text_digest=text_digest(malformed),
            salvage_result=result,
        )
        sample_errors = validate_canonical_s13g_payload(canonical, S13I_RETRY_SCENARIO_ID)
        if sample_errors:
            errors.append(f"S13j sample salvaged payload failed canonical validation: {sample_errors[:3]}")
        provenance = canonical.get("adapter_provenance") if isinstance(canonical, dict) else {}
        if not isinstance(provenance, dict) or provenance.get("salvage_generated_fields_are_not_model_generated") is not True:
            errors.append("S13j salvage provenance must mark salvage-generated fields as not model-generated")

    for policy in S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES:
        if policy.route != PUBLIC_API_DEV_ROUTE or policy.provider != REQUIRED_PROVIDER:
            errors.append(f"{policy.scenario_id}: route/provider mismatch")
        should_salvage = policy.scenario_id == S13I_RETRY_SCENARIO_ID
        if policy.salvage_required is not should_salvage:
            errors.append(f"{policy.scenario_id}: salvage_required mismatch")
        if policy.reuse_prior_s13i_output is not (not should_salvage):
            errors.append(f"{policy.scenario_id}: reuse_prior_s13i_output mismatch")
        for name, value in {
            "calls_gigachat": policy.calls_gigachat,
            "completed_human_review_results_present": policy.completed_human_review_results_present,
            "selected_parity_claim_supported_now": policy.selected_parity_claim_supported_now,
            "server3_local_intranet_verified": policy.server3_local_intranet_verified,
            "kimi_level_claimed": policy.kimi_level_claimed,
            "credential_values_recorded": policy.credential_values_recorded,
        }.items():
            if value is not False:
                errors.append(f"{policy.scenario_id}: {name} must be false")
    return errors


def executive_memo_salvage_report() -> dict[str, Any]:
    errors = validate_executive_memo_salvage_contract()
    salvage_policies = [policy for policy in S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES if policy.salvage_required]
    reused_policies = [policy for policy in S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES if policy.reuse_prior_s13i_output]
    return {
        "status": "ready" if not errors else "not_ready",
        "workflow_id": S13J_WORKFLOW_ID,
        "s_phase": S13J_PHASE_ID,
        "executive_memo_salvage_ready_by_s13j": not errors,
        "scenario_count": len(S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES),
        "salvage_scenario_count": len(salvage_policies),
        "salvage_scenario_ids": [policy.scenario_id for policy in salvage_policies],
        "reused_canonical_scenario_count": len(reused_policies),
        "expected_prior_canonical_valid_count_by_s13j": S13J_EXPECTED_PRIOR_CANONICAL_VALID_COUNT,
        "expected_final_canonical_valid_count_by_s13j": S13J_EXPECTED_FINAL_CANONICAL_VALID_COUNT,
        "route_required_by_s13j": PUBLIC_API_DEV_ROUTE,
        "provider_required_by_s13j": REQUIRED_PROVIDER,
        "requires_prior_s13i_live_zip_by_s13j": True,
        "calls_gigachat_by_s13j_static_check": False,
        "deterministic_salvage_only_by_s13j": True,
        "reuses_prior_s13i_canonical_valid_outputs_by_s13j": True,
        "preserves_original_response_digest_by_s13j": True,
        "salvage_manifest_required_by_s13j": True,
        "salvage_generated_fields_marked_not_model_generated_by_s13j": True,
        "completed_human_review_results_present_by_s13j": False,
        "selected_offline_workflow_parity_claim_supported_now_by_s13j": False,
        "server3_local_intranet_route_verified_by_s13j": False,
        "public_api_dev_route_is_not_server3_proof_by_s13j": True,
        "credential_values_recorded_by_s13j": False,
        "kimi_level_claimed_by_s13j": False,
        "whole_project_kimi_level_supported": False,
        "api_endpoint_added_by_s13j": False,
        "db_schema_migration_added_by_s13j": False,
        "frontend_runtime_changed_by_s13j": False,
        "dependency_versions_changed_by_s13j": False,
        "dockerfiles_changed_by_s13j": False,
        "next_recommended_step": "Run S13j against the failed S13i live ZIP and export human review packet only if merged canonical count reaches 12/12.",
        "salvage_actions": list(S13J_SALVAGE_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_S13J_ACTIONS),
        "contract": {"policies": [policy.as_dict() for policy in S13J_EXECUTIVE_MEMO_SALVAGE_POLICIES]},
        "errors": errors,
    }
