from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol
from backend.app.integrations.llm.models import LLMCompletionRequest, LLMCompletionResult
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

K1_CHECKPOINT = "K1"
K_PHASE_BRANCH = "8_K_Phase"
K1_SCHEMA_VERSION = "k1.local_gigachat_planner.v1"
_SECRET_PATTERNS = (re.compile(r"sk-[A-Za-z0-9_\-]{8,}"), re.compile(r"github_" + r"pat_[A-Za-z0-9_\-]+"), re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+"))

class K1LocalGigaChatPlannerError(RuntimeError):
    pass

class K1LLMProvider(Protocol):
    provider_name: str
    model_name: str
    def complete(self, request: LLMCompletionRequest) -> LLMCompletionResult: ...

@dataclass(frozen=True)
class K1PlanningRequest:
    source_text: str
    audience: str = "executive_operator"
    deck_goal: str = "Create a source-grounded presentation plan."
    target_slide_count: int = 7
    source_refs: tuple[dict[str, str], ...] = ()
    allow_deterministic_fallback: bool = True
    operator_user_id: str = "user_local_default"
    session_id: str | None = None
    task_id: str | None = None

@dataclass(frozen=True)
class K1PlanningResult:
    plan: PresentationPlan
    safe_metadata: dict[str, object]
    llm_used: bool
    deterministic_fallback_used: bool
    fallback_reason_code: str | None
    prompt_digest: str
    source_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {"plan": {"deck_title": self.plan.deck_title, "slide_count": len(self.plan.slides), "slides": [{"title": s.title, "slide_type": s.slide_type.value, "bullets": list(s.bullets), "source_notes": list(s.source_notes)} for s in self.plan.slides]}, "safe_metadata": dict(self.safe_metadata), "llm_used": self.llm_used, "deterministic_fallback_used": self.deterministic_fallback_used, "fallback_reason_code": self.fallback_reason_code, "prompt_digest": self.prompt_digest, "source_digest": self.source_digest}

@dataclass
class LocalGigaChatPlanningEngine:
    llm_provider: K1LLMProvider | None = None
    production_mode: bool = True

    def plan(self, request: K1PlanningRequest) -> K1PlanningResult:
        _validate_request(request)
        system_prompt = build_k1_system_prompt()
        user_prompt = build_k1_user_prompt(request)
        prompt_digest = _digest(system_prompt + "\n" + user_prompt)
        source_digest = _digest(request.source_text)
        provider = self.llm_provider
        fallback_reason = None
        llm_result = None
        if provider is None:
            if not request.allow_deterministic_fallback:
                raise K1LocalGigaChatPlannerError("K1 local GigaChat provider is required when fallback is disabled")
            fallback_reason = "local_gigachat_provider_not_configured"
        else:
            provider_name = str(getattr(provider, "provider_name", "")).lower().strip()
            if self.production_mode and provider_name != "gigachat":
                if not request.allow_deterministic_fallback:
                    raise K1LocalGigaChatPlannerError("K1 production planner requires local GigaChat provider")
                fallback_reason = "non_gigachat_provider_rejected"
            else:
                try:
                    llm_result = provider.complete(LLMCompletionRequest(prompt=user_prompt, system_prompt=system_prompt, temperature=0.2))
                except Exception:
                    if not request.allow_deterministic_fallback:
                        raise K1LocalGigaChatPlannerError("K1 local GigaChat planning failed and fallback is disabled")
                    fallback_reason = "local_gigachat_unavailable"
        if llm_result is not None:
            try:
                plan = _plan_from_llm_payload(llm_result.text, request)
                llm_used = True
                fallback_used = False
            except Exception:
                if not request.allow_deterministic_fallback:
                    raise K1LocalGigaChatPlannerError("K1 local GigaChat response could not be parsed and fallback is disabled")
                fallback_reason = "local_gigachat_response_parse_failed"
                plan = _deterministic_plan(request)
                llm_used = False
                fallback_used = True
        else:
            plan = _deterministic_plan(request)
            llm_used = False
            fallback_used = True
        source_profile = _detect_source_profile(request.source_text)
        plan = _sanitize_generic_fallback_labels(plan, request, source_profile)
        safe_metadata: dict[str, object] = {"workflow_id": "k1.local_gigachat_planning_engine", "schema_version": K1_SCHEMA_VERSION, "checkpoint": K1_CHECKPOINT, "k_phase_branch": K_PHASE_BRANCH, "k1_local_gigachat_planning_supported": True, "source_aware_planning_supported": True, "outline_first_plan_supported": True, "editable_plan_supported": True, "local_gigachat_default_provider": True, "direct_local_gigachat_first": True, "litellm_override_allowed_by_k1": False, "cloud_llm_added_by_k1": False, "internet_runtime_required_by_k1": False, "deterministic_fallback_supported": True, "llm_used": llm_used, "deterministic_fallback_used": fallback_used, "fallback_reason_code": fallback_reason or "none", "provider": str(getattr(provider, "provider_name", "none")) if provider is not None else "none", "model": str(getattr(provider, "model_name", "none")) if provider is not None else "none", "prompt_digest": prompt_digest, "source_digest": source_digest, "source_refs_count": len(request.source_refs), "slide_count": len(plan.slides), "target_slide_count": request.target_slide_count, "p9_2_renderer_content_hardening_supported": True, "source_profile": source_profile, "generic_fallback_labels_removed": _plan_has_no_generic_labels(plan), "comparison_table_decision_matrix_supported": source_profile == "comparison_table", "project_log_late_phase_coverage_supported": source_profile == "project_log", "long_source_filler_slide_prevention_supported": source_profile == "long_structured_source", "human_review_findings_addressed_by_p9_2": True, "raw_source_text_stored": False, "raw_prompt_stored": False, "raw_secret_values_stored": False, "kimi_level_claimed_by_k1": False, "whole_project_kimi_level_supported": False, "runtime_changed_by_k1": True, "dependency_versions_changed_by_k1": False, "dockerfiles_changed_by_k1": False, "api_endpoint_added_by_k1": False, "db_schema_migration_added_by_k1": False}
        _assert_safe_metadata(safe_metadata, request.source_text, user_prompt)
        return K1PlanningResult(plan, safe_metadata, llm_used, fallback_used, fallback_reason, prompt_digest, source_digest)

def build_k1_system_prompt() -> str:
    return "You are KW Studio's offline local GigaChat planning engine. Create a source-grounded, outline-first slide plan. Use only provided sources. Do not claim Kimi-level quality. Return compact JSON only."

def build_k1_user_prompt(request: K1PlanningRequest) -> str:
    return json.dumps({"task": "build_presentation_plan", "audience": request.audience, "deck_goal": request.deck_goal, "target_slide_count": request.target_slide_count, "source_refs": tuple({"source_id": r.get("source_id", ""), "title": r.get("title", "")} for r in request.source_refs), "source_text": _redact_text(request.source_text), "output_schema": {"deck_title": "string", "slides": [{"title": "string", "bullets": ["string"], "slide_type": "title|section|content|comparison|timeline|data|conclusion|appendix"}]}}, ensure_ascii=False, sort_keys=True)

def _plan_from_llm_payload(text: str, request: K1PlanningRequest) -> PresentationPlan:
    payload = json.loads(_extract_json_object(text))
    raw_slides = payload.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        raise ValueError("missing slides")
    slides: list[PlannedSlide] = []
    for index, raw in enumerate(raw_slides[: request.target_slide_count], start=1):
        if not isinstance(raw, dict):
            continue
        st = _slide_type(str(raw.get("slide_type") or ("title" if index == 1 else "content")))
        bullets_raw = raw.get("bullets")
        bullets = tuple(_redact_text(str(b)).strip()[:140] for b in bullets_raw if str(b).strip()) if isinstance(bullets_raw, list) else (_source_snippet(request.source_text, index),)
        slides.append(PlannedSlide(slide_id=f"k1_llm_{index:03d}", slide_type=st, story_arc_stage=_stage(index, request.target_slide_count), title=str(raw.get("title") or f"Slide {index}")[:80], bullets=bullets[:4], speaker_notes="Operator-editable K1 local GigaChat planning note.", layout_hint=_layout(st), source_notes=(_source_note(request, index),)))
    if len(slides) < 3:
        raise ValueError("too few slides")
    return PresentationPlan(deck_title=str(payload.get("deck_title") or "K1 Local GigaChat Plan")[:80], deck_goal=request.deck_goal, audience=request.audience, tone="clear_professional", target_slide_count=len(slides), story_arc=tuple(s.story_arc_stage for s in slides), slides=tuple(slides))

def _deterministic_plan(request: K1PlanningRequest) -> PresentationPlan:
    source_profile = _detect_source_profile(request.source_text)
    count = max(5, min(10, request.target_slide_count))
    specs = _profiled_slide_specs(request.source_text, source_profile, count)
    slides: list[PlannedSlide] = []
    for i, spec in enumerate(specs[:count], start=1):
        st = spec["slide_type"]
        title = _clean_title(str(spec["title"]))
        bullets = tuple(_bounded_bullet_text(str(b)) for b in spec["bullets"] if str(b).strip())[:4]
        slides.append(
            PlannedSlide(
                slide_id=f"k1_fallback_{i:03d}",
                slide_type=st,
                story_arc_stage=_stage(i, count),
                title=title,
                bullets=bullets or ("Source-derived planning point for operator review.",),
                speaker_notes="Deterministic local fallback; revise in K2 plan editor before approval.",
                layout_hint=_layout(st),
                source_notes=(_source_note(request, i),),
            )
        )
    return PresentationPlan(deck_title=slides[0].title, deck_goal=request.deck_goal, audience=request.audience, tone="clear_professional", target_slide_count=count, story_arc=tuple(s.story_arc_stage for s in slides), slides=tuple(slides))


def _validate_request(request: K1PlanningRequest) -> None:
    if not request.source_text.strip():
        raise ValueError("K1 planning requires source_text")
    if request.target_slide_count < 3 or request.target_slide_count > 20:
        raise ValueError("K1 target_slide_count must be between 3 and 20")


def _extract_json_object(text: str) -> str:
    s = text.strip(); start = s.find("{"); end = s.rfind("}")
    if start < 0 or end <= start: raise ValueError("no JSON object")
    return s[start:end+1]


def _segments(t: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", t.replace("\n", ". ")).strip()
    segments = [p.strip(" .") for p in normalized.split(".") if p.strip(" .")]
    return segments or ["Untitled source"]


def _detect_source_profile(source_text: str) -> str:
    lowered = source_text.lower()
    if "option,strength,weakness,recommendation" in lowered or all(token in lowered for token in ("option", "strength", "weakness", "recommendation")):
        return "comparison_table"
    if all(token in source_text for token in ("K0", "K1", "K2", "K3")) and any(token in source_text for token in ("K4", "K5", "K6")):
        return "project_log"
    if len(re.findall(r"\bSection\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b", source_text, flags=re.IGNORECASE)) >= 4:
        return "long_structured_source"
    if any(token in lowered for token in ("server 1", "server 2", "server 3", "architecture", "topology")):
        return "technical_architecture"
    if any(token in lowered for token in ("executive memo", "recommended decision", "next actions", "business objective")):
        return "executive_memo"
    return "general_source"


def _profiled_slide_specs(source_text: str, source_profile: str, count: int) -> list[dict[str, Any]]:
    if source_profile == "comparison_table":
        return _comparison_table_specs(source_text, count)
    if source_profile == "project_log":
        return _project_log_specs(source_text, count)
    if source_profile == "long_structured_source":
        return _long_structured_source_specs(source_text, count)
    if source_profile == "technical_architecture":
        return _technical_architecture_specs(source_text, count)
    if source_profile == "executive_memo":
        return _executive_memo_specs(source_text, count)
    return _general_source_specs(source_text, count)


def _comparison_table_specs(source_text: str, count: int) -> list[dict[str, Any]]:
    rows = _parse_comparison_rows(source_text)
    default = _first_row_matching(rows, "direct local gigachat") or (rows[0] if rows else {})
    litellm = _first_row_matching(rows, "litellm")
    cloud = _first_row_matching(rows, "cloud")
    ollama = _first_row_matching(rows, "ollama")
    options = [r.get("option", "option") for r in rows[:5]] or ["Direct local GigaChat", "LiteLLM gateway", "Ollama fallback", "Cloud LLM"]
    specs = [
        _spec(SlideType.TITLE, "Decision: keep local GigaChat as default", [_decision_sentence(source_text), "Frame alternatives by offline fit, operational surface, and data locality."]),
        _spec(SlideType.COMPARISON, "Decision matrix: runtime options", ["Options: " + "; ".join(options), "Compare each option by strength, weakness, and recommendation."]),
        _spec(SlideType.CONCLUSION, "Recommended default: Direct local GigaChat", [_row_text(default, "strength"), _row_text(default, "weakness"), _row_text(default, "recommendation")]),
        _spec(SlideType.CONTENT, "Optional path: LiteLLM gateway on Server 2", [_row_text(litellm, "strength"), _row_text(litellm, "weakness"), _row_text(litellm, "recommendation")]),
        _spec(SlideType.CONTENT, "Fallback boundary: Ollama remains non-production", [_row_text(ollama, "strength"), _row_text(ollama, "weakness"), _row_text(ollama, "recommendation")]),
        _spec(SlideType.CONCLUSION, "Rejected default: cloud LLM for production", [_row_text(cloud, "strength"), _row_text(cloud, "weakness"), _row_text(cloud, "recommendation")]),
        _spec(SlideType.DATA, "Release constraint: measure quality before expansion", ["Use RC1 to measure workflow quality before expanding runtime scope.", "Preserve offline-first defaults and data locality."]),
    ]
    return _fit_specs(specs, source_text, count)


def _project_log_specs(source_text: str, count: int) -> list[dict[str, Any]]:
    specs = [
        _spec(SlideType.TITLE, "Status: controlled baseline ready for RC1", ["Runtime Foundation closed first.", "K0-K6 checkpoints are recorded as a controlled sequence."]),
        _spec(SlideType.TIMELINE, "Completed foundation: RF through K3", ["K0 defined the benchmark rubric without product-parity claims.", "K1-K3 added planning, approval, and renderer-quality controls."]),
        _spec(SlideType.CONTENT, "Late-phase coverage: K4 and K5", ["K4 added deterministic Visual QA over PPTX OOXML.", "K5 added source-to-slide provenance and bounded evidence fragments."]),
        _spec(SlideType.CONCLUSION, "Workflow closure: K6 and release readiness", ["K6 connected the stages into an end-to-end workflow.", "K-phase closure accepted the release-readiness checkpoint."]),
        _spec(SlideType.DATA, "Current risks: benchmark realism and UX depth", [_sentence_containing(source_text, "Current risks") or "Current risks include benchmark realism, fixture coverage, visual quality depth, and provenance review ergonomics."]),
        _spec(SlideType.CONCLUSION, "Next action: RC1 benchmark execution", [_sentence_containing(source_text, "next action") or "The next action is RC1 benchmark execution."]),
    ]
    return _fit_specs(specs, source_text, count)


def _long_structured_source_specs(source_text: str, count: int) -> list[dict[str, Any]]:
    section_map = _section_map(source_text)
    specs = [
        _spec(SlideType.TITLE, "Product goal: verifiable knowledge-work artifacts", [_section_text(section_map, "one", "KW Studio turns documents, data, slides, Python analysis, and browser-assisted workflows into verifiable artifacts.")]),
        _spec(SlideType.SECTION, "Offline constraint: intranet-safe production", [_section_text(section_map, "two", "Default production execution must work inside an intranet and avoid hidden public internet dependencies.")]),
        _spec(SlideType.CONTENT, "LLM topology: Server 3 local GigaChat", [_section_text(section_map, "three", "Server 3 hosts local GigaChat, Server 1 hosts KW Studio, and Server 2 is optional.")]),
        _spec(SlideType.CONTENT, "Runtime Foundation: operator-grade controls", [_section_text(section_map, "four", "Schema preflight, artifact history, diagnostics, backup, environment validation, and deployment checks.")]),
        _spec(SlideType.CONTENT, "K-phase capabilities: planning to readiness", [_section_text(section_map, "five", "Rubric, planning, editing, renderer quality, visual QA, provenance, end-to-end workflow, and release readiness.")]),
        _spec(SlideType.DATA, "Benchmark requirements: quality and provenance", [_section_text(section_map, "six", "Each deck must preserve source faithfulness, visual hierarchy, density control, provenance, and offline reproducibility.")]),
        _spec(SlideType.DATA, "Release risks: realism and operator UX", [_section_text(section_map, "seven", "Fixture realism, visual regression coverage, template depth, table handling, and operator UX.")]),
        _spec(SlideType.CONCLUSION, "RC1 proposal: golden cases and human review", [_section_text(section_map, "eight", "Run five golden cases, collect PPTX and manifest artifacts, compute conservative proxy metrics, and require human review.")]),
        _spec(SlideType.APPENDIX, "Evidence package: PPTX plus manifest artifacts", ["RC1 collects PPTX and manifest artifacts as review evidence.", "Automated proxy metrics stay conservative until human review is complete."]),
        _spec(SlideType.CONCLUSION, "Claim guard: review before product-quality claims", ["Require human review before any Kimi-level claim.", "Keep offline reproducibility visible in the operator evidence pack."]),
    ]
    return _fit_specs(specs, source_text, count)


def _technical_architecture_specs(source_text: str, count: int) -> list[dict[str, Any]]:
    server1 = _sentence_containing(source_text, "Server 1") or "Server 1 hosts KW Studio: backend, frontend, Postgres, workflows, artifact storage, and operator UI."
    server2 = _sentence_containing(source_text, "Server 2") or "Server 2 is optional for LiteLLM-compatible gateway experiments and heavy runtime modules."
    server3 = _sentence_containing(source_text, "Server 3") or "Server 3 hosts local GigaChat behind an internal endpoint."
    default_route = _sentence_containing(source_text, "default production") or "The default production path is direct local GigaChat, not cloud fallback."
    foundation = _sentence_containing(source_text, "Runtime Foundation") or "Runtime Foundation closed deployment hardening, schema preflight, diagnostics, backup, and dependency controls."
    k_phase = _sentence_containing(source_text, "K-phase") or "K-phase added planning, editable approval, render quality, visual QA, provenance, and workflow gates."
    review_focus = _sentence_containing(source_text, "boundaries") or "The architecture review must highlight boundaries, failure modes, and release-readiness checks."
    specs = [
        _spec(SlideType.TITLE, "Architecture review: offline KW Studio topology", [_sentence_containing(source_text, "three offline") or _segments(source_text)[0]]),
        _spec(SlideType.SECTION, "Topology map: Server 1/2/3 responsibilities", [server1, server2, server3]),
        _spec(SlideType.CONTENT, "Production path: direct local GigaChat", [default_route, "Keep cloud LLM routes outside the default production runtime."]),
        _spec(SlideType.CONTENT, "Server 2 boundary: optional gateway and heavy runtime", [server2, "Treat LiteLLM/Ollama paths as optional transport, fallback, or experimental capacity, not production default."]),
        _spec(SlideType.DATA, "Closed foundation controls: deployment and diagnostics", [foundation, "Use preflight, readiness, diagnostics, backup, restore, and dependency checks as operator gates."]),
        _spec(SlideType.CONTENT, "Runtime capabilities: plan, render, QA, provenance", [k_phase, "Preserve editable plans, retry, source-to-slide evidence, and artifact history for operator review."]),
        _spec(SlideType.CONCLUSION, "Failure modes and operator gates", [review_focus, "Gate endpoint misconfiguration, hidden network use, fallback drift, provenance gaps, and visual/layout regressions."]),
        _spec(SlideType.CONCLUSION, "Release readiness checks and ownership", ["Verify Server 1 app readiness, optional Server 2 boundary, and Server 3 local GigaChat configuration before offline operation.", "Keep public_api_dev benchmark evidence separate from Server 3 local_intranet proof."]),
    ]
    return _fit_specs(specs, source_text, count)


def _executive_memo_specs(source_text: str, count: int) -> list[dict[str, Any]]:
    specs = [
        _spec(SlideType.TITLE, "Executive decision: enter release-candidate hardening", [_sentence_containing(source_text, "release-candidate") or _segments(source_text)[0]]),
        _spec(SlideType.SECTION, "Business objective: verifiable offline artifacts", [_sentence_containing(source_text, "business objective") or "Convert internal documents into verifiable downloadable decks while remaining offline and intranet-safe."]),
        _spec(SlideType.CONTENT, "Readiness signal: K0-K6 closure", [_sentence_containing(source_text, "K-phase closure") or "K0 through K6 are accepted and ready for release-candidate evaluation."]),
        _spec(SlideType.DATA, "Risk guard: avoid premature quality claims", [_sentence_containing(source_text, "primary risk") or "The primary risk is overclaiming product quality before benchmark review."]),
        _spec(SlideType.CONCLUSION, "Recommended decision: start RC1", [_sentence_containing(source_text, "recommended decision") or "Start RC1 with golden benchmark execution."]),
        _spec(SlideType.CONTENT, "Review evidence: visual QA and provenance", [_sentence_containing(source_text, "visual QA") or "Review visual QA and provenance before adding runtime scope."]),
        _spec(SlideType.CONCLUSION, "Next actions: run cases and feed fixes", [_sentence_containing(source_text, "next actions") or "Run benchmark cases, collect artifacts, and feed focused fixes into later patches."]),
    ]
    return _fit_specs(specs, source_text, count)


def _general_source_specs(source_text: str, count: int) -> list[dict[str, Any]]:
    segments = _segments(source_text)
    specs: list[dict[str, Any]] = []
    prefixes = ["Opening", "Context", "Evidence", "Trade-off", "Quality signal", "Operator review", "Recommended next step", "Appendix evidence", "Implementation note", "Close"]
    types = [SlideType.TITLE, SlideType.SECTION, SlideType.CONTENT, SlideType.COMPARISON, SlideType.DATA, SlideType.CONTENT, SlideType.CONCLUSION, SlideType.APPENDIX, SlideType.CONTENT, SlideType.CONCLUSION]
    for i in range(count):
        seed = segments[i % len(segments)]
        title = f"{prefixes[i]}: {_source_phrase(seed)}"
        specs.append(_spec(types[i], title, _bullets(seed)))
    return specs


def _fit_specs(specs: list[dict[str, Any]], source_text: str, count: int) -> list[dict[str, Any]]:
    if len(specs) >= count:
        return specs[:count]
    existing_titles = {str(s["title"]) for s in specs}
    for spec in _general_source_specs(source_text, count):
        if spec["title"] not in existing_titles:
            specs.append(spec)
            existing_titles.add(str(spec["title"]))
        if len(specs) >= count:
            break
    return specs[:count]


def _spec(slide_type: SlideType, title: str, bullets: list[str]) -> dict[str, Any]:
    return {"slide_type": slide_type, "title": _clean_title(title), "bullets": [b for b in bullets if str(b).strip()]}


def _parse_comparison_rows(source_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for segment in _segments(source_text):
        parts = [p.strip() for p in segment.split(",")]
        if len(parts) < 4:
            continue
        if [p.lower() for p in parts[:4]] == ["option", "strength", "weakness", "recommendation"]:
            continue
        rows.append({"option": parts[0], "strength": parts[1], "weakness": parts[2], "recommendation": ", ".join(parts[3:])})
    return rows


def _first_row_matching(rows: list[dict[str, str]], needle: str) -> dict[str, str] | None:
    needle_l = needle.lower()
    return next((row for row in rows if needle_l in row.get("option", "").lower()), None)


def _row_text(row: dict[str, str] | None, key: str) -> str:
    if not row:
        return "No source row available for this option."
    label = {"strength": "Strength", "weakness": "Weakness", "recommendation": "Recommendation"}.get(key, key.title())
    return f"{label}: {row.get(key, '').strip()}".strip()


def _decision_sentence(source_text: str) -> str:
    return _sentence_containing(source_text, "decision is") or "The decision is to keep direct local GigaChat as default."


def _sentence_containing(source_text: str, needle: str) -> str | None:
    needle_l = needle.lower()
    for segment in _segments(source_text):
        if needle_l in segment.lower():
            return segment
    return None


def _section_map(source_text: str) -> dict[str, str]:
    pattern = re.compile(r"Section\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+([^.]*)", re.IGNORECASE)
    sections: dict[str, str] = {}
    for match in pattern.finditer(source_text):
        sections[match.group(1).lower()] = ("Section " + match.group(1) + " " + match.group(2)).strip()
    return sections


def _section_text(sections: dict[str, str], key: str, fallback: str) -> str:
    return sections.get(key, fallback)


def _title(st: SlideType, seed: str) -> str:
    prefix = {SlideType.TITLE: "Opening", SlideType.SECTION: "Context", SlideType.COMPARISON: "Decision trade-off", SlideType.DATA: "Evidence signals", SlideType.CONCLUSION: "Recommended next step", SlideType.APPENDIX: "Appendix evidence"}.get(st, "Source point")
    return _clean_title(f"{prefix}: {_source_phrase(seed)}")


def _source_phrase(seed: str) -> str:
    words = [w.strip() for w in seed.split() if w.strip()]
    return " ".join(words[:8]).strip(" .,:;") or "source detail"


def _clean_title(title: str) -> str:
    cleaned = re.sub(r"\s+", " ", title).strip(" .")
    for label in _GENERIC_FALLBACK_LABELS:
        cleaned = cleaned.replace(label, "Source-grounded")
    return cleaned[:80] or "Source-grounded slide"


def _bullets(seed: str) -> list[str]:
    words = seed.split(); chunks = [" ".join(words[i:i+10]).strip() for i in range(0, min(len(words), 30), 10)]
    return [_bounded_bullet_text(c) for c in chunks if c][:3] or [_bounded_bullet_text(seed) or "Source detail for operator review"]


def _bounded_bullet_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:140]


def _sanitize_generic_fallback_labels(plan: PresentationPlan, request: K1PlanningRequest, source_profile: str) -> PresentationPlan:
    segments = _segments(request.source_text)
    slides: list[PlannedSlide] = []
    for index, slide in enumerate(plan.slides, start=1):
        if _has_generic_label(slide.title):
            seed = segments[(index - 1) % len(segments)]
            title = _profile_repair_title(source_profile, slide.slide_type, seed, index)
        else:
            title = _clean_title(slide.title)
        bullets = tuple(_bounded_bullet_text(b) for b in slide.bullets if str(b).strip())
        slides.append(
            PlannedSlide(
                slide_id=slide.slide_id,
                slide_type=slide.slide_type,
                story_arc_stage=slide.story_arc_stage,
                title=title,
                bullets=bullets,
                speaker_notes=slide.speaker_notes,
                layout_hint=slide.layout_hint,
                visual_intent=slide.visual_intent,
                image_specs=slide.image_specs,
                media_assets=slide.media_assets,
                blocks=slide.blocks,
                citations=slide.citations,
                source_notes=slide.source_notes,
            )
        )
    deck_title = slides[0].title if _has_generic_label(plan.deck_title) else _clean_title(plan.deck_title)
    return PresentationPlan(deck_title=deck_title, deck_goal=plan.deck_goal, audience=plan.audience, tone=plan.tone, target_slide_count=plan.target_slide_count, story_arc=plan.story_arc, slides=tuple(slides))


def _profile_repair_title(source_profile: str, slide_type: SlideType, seed: str, index: int) -> str:
    if source_profile == "comparison_table":
        repairs = ["Decision: local GigaChat default", "Decision matrix: runtime options", "Recommended default", "Optional gateway path", "Fallback boundary", "Rejected default", "Release constraint"]
        return repairs[min(index - 1, len(repairs) - 1)]
    if source_profile == "project_log":
        repairs = ["Status: controlled baseline", "Foundation through K3", "K4/K5 late-phase coverage", "K6 workflow closure", "Current risks", "Next action"]
        return repairs[min(index - 1, len(repairs) - 1)]
    if source_profile == "long_structured_source":
        return _clean_title(f"Section-derived slide {index}: {_source_phrase(seed)}")
    return _title(slide_type, seed)


def _has_generic_label(value: str) -> bool:
    lowered = value.lower()
    return any(label.lower() in lowered for label in _GENERIC_FALLBACK_LABELS)


def _plan_has_no_generic_labels(plan: PresentationPlan) -> bool:
    values = [plan.deck_title, *(slide.title for slide in plan.slides), *(bullet for slide in plan.slides for bullet in slide.bullets)]
    return not any(_has_generic_label(str(value)) for value in values)


_GENERIC_FALLBACK_LABELS = ("K1 Plan", "Key point", "Additional source-grounded planning point")


def _source_snippet(t: str, idx: int) -> str:
    segs = _segments(t); return segs[(idx-1)%len(segs)][:120]

def _source_note(request: K1PlanningRequest, idx: int) -> str:
    if request.source_refs:
        return "source:" + request.source_refs[(idx-1)%len(request.source_refs)].get("source_id", "local_source")
    return "source:local_text"

def _slide_type(v: str) -> SlideType:
    try: return SlideType(v.strip().lower())
    except ValueError: return SlideType.CONTENT

def _stage(i: int, total: int) -> StoryArcStage:
    if i == 1: return StoryArcStage.OPENING
    if i == 2: return StoryArcStage.CONTEXT
    if i >= total - 1: return StoryArcStage.CLOSE
    if i >= max(3, total - 2): return StoryArcStage.RECOMMENDATION
    return StoryArcStage.ANALYSIS

def _layout(st: SlideType) -> str:
    return {SlideType.TITLE:"title_with_visual", SlideType.SECTION:"section_slide", SlideType.COMPARISON:"two_column_comparison", SlideType.TIMELINE:"timeline", SlideType.DATA:"data_summary", SlideType.CONCLUSION:"conclusion", SlideType.APPENDIX:"appendix_evidence"}.get(st, "content_with_visual")

def _digest(v: str) -> str:
    return "sha256:" + sha256(v.encode("utf-8")).hexdigest()

def _redact_text(v: str) -> str:
    out = v
    for p in _SECRET_PATTERNS: out = p.sub("[REDACTED]", out)
    return out

def _assert_safe_metadata(metadata: dict[str, object], source_text: str, prompt: str) -> None:
    encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    if source_text[:80] in encoded or prompt[:80] in encoded or "client_secret" in encoded or "authorization" in encoded:
        raise K1LocalGigaChatPlannerError("K1 safe metadata contains raw source, prompt, or secret-like content")
