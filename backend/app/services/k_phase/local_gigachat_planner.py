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
        safe_metadata: dict[str, object] = {"workflow_id": "k1.local_gigachat_planning_engine", "schema_version": K1_SCHEMA_VERSION, "checkpoint": K1_CHECKPOINT, "k_phase_branch": K_PHASE_BRANCH, "k1_local_gigachat_planning_supported": True, "source_aware_planning_supported": True, "outline_first_plan_supported": True, "editable_plan_supported": True, "local_gigachat_default_provider": True, "direct_local_gigachat_first": True, "litellm_override_allowed_by_k1": False, "cloud_llm_added_by_k1": False, "internet_runtime_required_by_k1": False, "deterministic_fallback_supported": True, "llm_used": llm_used, "deterministic_fallback_used": fallback_used, "fallback_reason_code": fallback_reason or "none", "provider": str(getattr(provider, "provider_name", "none")) if provider is not None else "none", "model": str(getattr(provider, "model_name", "none")) if provider is not None else "none", "prompt_digest": prompt_digest, "source_digest": source_digest, "source_refs_count": len(request.source_refs), "slide_count": len(plan.slides), "target_slide_count": request.target_slide_count, "raw_source_text_stored": False, "raw_prompt_stored": False, "raw_secret_values_stored": False, "kimi_level_claimed_by_k1": False, "whole_project_kimi_level_supported": False, "runtime_changed_by_k1": True, "dependency_versions_changed_by_k1": False, "dockerfiles_changed_by_k1": False, "api_endpoint_added_by_k1": False, "db_schema_migration_added_by_k1": False}
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
    segs = _segments(request.source_text)
    count = max(5, min(10, request.target_slide_count))
    while len(segs) < count:
        segs.append(f"Additional source-grounded planning point {len(segs)+1}")
    types = [SlideType.TITLE, SlideType.SECTION, SlideType.CONTENT, SlideType.COMPARISON, SlideType.DATA, SlideType.CONTENT, SlideType.CONCLUSION, SlideType.APPENDIX, SlideType.CONTENT, SlideType.CONCLUSION]
    slides = []
    for i in range(count):
        st = types[i] if i < len(types) else SlideType.CONTENT
        seed = segs[i]
        slides.append(PlannedSlide(slide_id=f"k1_fallback_{i+1:03d}", slide_type=st, story_arc_stage=_stage(i+1, count), title=_title(st, seed), bullets=tuple(_bullets(seed)), speaker_notes="Deterministic local fallback; revise in K2 plan editor before approval.", layout_hint=_layout(st), source_notes=(_source_note(request, i+1),)))
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
    return [p.strip(" .") for p in t.replace("\n", ". ").split(".") if p.strip(" .")] or ["Untitled source"]

def _title(st: SlideType, seed: str) -> str:
    prefix = {SlideType.TITLE: "K1 Plan", SlideType.SECTION: "Context", SlideType.COMPARISON: "Decision trade-off", SlideType.DATA: "Evidence signals", SlideType.CONCLUSION: "Recommended next step", SlideType.APPENDIX: "Appendix evidence"}.get(st, "Key point")
    return f"{prefix}: {seed[:42]}"[:80]

def _bullets(seed: str) -> list[str]:
    words = seed.split(); chunks = [" ".join(words[i:i+10]).strip() for i in range(0, min(len(words), 30), 10)]
    return [c for c in chunks if c][:3] or [seed[:80] or "No source detail provided"]

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
