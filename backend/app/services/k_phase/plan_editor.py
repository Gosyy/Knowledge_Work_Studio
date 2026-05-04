from __future__ import annotations

import json
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any
from uuid import uuid4

from backend.app.services.slides_service.image_pipeline import VisualIntent
from backend.app.services.slides_service.outline import PresentationPlan, PlannedSlide, SlideType, StoryArcStage

K2_CHECKPOINT = "K2"
K2_SCHEMA_VERSION = "k2.plan_editor_workflow.v1"
K_PHASE_BRANCH = "8_K_Phase"
_ALLOWED_RENDER_MODES = {"adaptive", "template"}
_ALLOWED_EVENT_TYPES = {
    "k2.plan_editor.session.created",
    "k2.plan_editor.edit.requested",
    "k2.plan_editor.slide.updated",
    "k2.plan_editor.render_mode.updated",
    "k2.plan_editor.approval.requested",
    "k2.plan_editor.approved",
}
_FORBIDDEN_SAFE_TEXT = ("password", "secret", "token", "api_key", "client_secret", "authorization")


class K2PlanEditorError(RuntimeError):
    pass


@dataclass(frozen=True)
class K2EvidenceLink:
    source_id: str
    title: str
    locator: str | None = None
    evidence_kind: str = "source_note"

    def as_safe_dict(self) -> dict[str, str | None]:
        return {
            "source_id": _safe_short_text(self.source_id, 80),
            "title": _safe_short_text(self.title, 120),
            "locator": _safe_short_text(self.locator or "", 120) or None,
            "evidence_kind": _safe_short_text(self.evidence_kind, 40),
        }


@dataclass(frozen=True)
class K2EditableSlide:
    slide_id: str
    slide_type: str
    story_arc_stage: str
    title: str
    bullets: tuple[str, ...]
    slide_intent: str
    evidence_links: tuple[K2EvidenceLink, ...] = ()
    visual_intent: str = "none"
    layout_hint: str | None = None
    render_mode: str = "adaptive"
    source_notes: tuple[str, ...] = ()

    def as_safe_dict(self) -> dict[str, object]:
        return {
            "slide_id": self.slide_id,
            "slide_type": self.slide_type,
            "story_arc_stage": self.story_arc_stage,
            "title": _safe_short_text(self.title, 160),
            "bullet_count": len(self.bullets),
            "slide_intent": _safe_short_text(self.slide_intent, 240),
            "evidence_link_count": len(self.evidence_links),
            "visual_intent": self.visual_intent,
            "layout_hint": _safe_short_text(self.layout_hint or "", 80) or None,
            "render_mode": self.render_mode,
            "source_note_count": len(self.source_notes),
        }


@dataclass(frozen=True)
class K2PlanEditorEvent:
    event_type: str
    sequence: int
    payload: dict[str, object]

    def as_safe_dict(self) -> dict[str, object]:
        return {"event_type": self.event_type, "sequence": self.sequence, "payload": dict(self.payload)}


@dataclass(frozen=True)
class K2SlidePatch:
    slide_id: str
    title: str | None = None
    bullets: tuple[str, ...] | None = None
    slide_intent: str | None = None
    evidence_links: tuple[K2EvidenceLink, ...] | None = None
    visual_intent: str | None = None
    layout_hint: str | None = None
    render_mode: str | None = None
    source_notes: tuple[str, ...] | None = None


@dataclass(frozen=True)
class K2PlanEditRequest:
    patches: tuple[K2SlidePatch, ...]
    change_summary: str
    operator_user_id: str = "user_local_default"
    retry_of_task_id: str | None = None
    requested_render_mode: str | None = None
    template_id: str | None = None


@dataclass(frozen=True)
class K2PlanEditorSession:
    session_id: str
    base_plan_digest: str
    version: int
    status: str
    deck_title: str
    deck_goal: str
    audience: str
    tone: str
    target_slide_count: int
    slides: tuple[K2EditableSlide, ...]
    render_mode: str
    template_id: str | None
    events: tuple[K2PlanEditorEvent, ...]
    operator_user_id: str
    retry_of_task_id: str | None = None

    def as_safe_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "base_plan_digest": self.base_plan_digest,
            "version": self.version,
            "status": self.status,
            "deck_title": _safe_short_text(self.deck_title, 160),
            "target_slide_count": self.target_slide_count,
            "slide_count": len(self.slides),
            "render_mode": self.render_mode,
            "template_id": self.template_id,
            "event_count": len(self.events),
            "operator_user_id": _safe_short_text(self.operator_user_id, 80),
            "retry_of_task_id": self.retry_of_task_id,
            "slides": [slide.as_safe_dict() for slide in self.slides],
        }


@dataclass(frozen=True)
class K2PlanEditorResult:
    session: K2PlanEditorSession
    approved_plan: PresentationPlan | None
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "session": self.session.as_safe_dict(),
            "approved_plan_present": self.approved_plan is not None,
            "safe_metadata": dict(self.safe_metadata),
        }


class K2PlanEditorWorkflow:
    def create_session(
        self,
        plan: PresentationPlan,
        *,
        operator_user_id: str = "user_local_default",
        render_mode: str = "adaptive",
        template_id: str | None = None,
        source_links_by_slide_id: dict[str, tuple[K2EvidenceLink, ...]] | None = None,
        retry_of_task_id: str | None = None,
    ) -> K2PlanEditorResult:
        _validate_render_mode(render_mode=render_mode, template_id=template_id)
        slides = tuple(
            _editable_slide_from_plan_slide(
                slide,
                evidence_links=(source_links_by_slide_id or {}).get(slide.slide_id, ()),
                render_mode=render_mode,
            )
            for slide in plan.slides
        )
        session_id = f"k2_plan_editor_{uuid4().hex}"
        events = (
            _event(
                sequence=1,
                event_type="k2.plan_editor.session.created",
                session_id=session_id,
                version=1,
                payload={
                    "slide_count": len(slides),
                    "render_mode": render_mode,
                    "template_id": template_id,
                    "retry_of_task_id": retry_of_task_id,
                },
            ),
        )
        session = K2PlanEditorSession(
            session_id=session_id,
            base_plan_digest=_plan_digest(plan),
            version=1,
            status="editing",
            deck_title=plan.deck_title,
            deck_goal=plan.deck_goal,
            audience=plan.audience,
            tone=plan.tone,
            target_slide_count=plan.target_slide_count,
            slides=slides,
            render_mode=render_mode,
            template_id=template_id,
            events=events,
            operator_user_id=operator_user_id,
            retry_of_task_id=retry_of_task_id,
        )
        return K2PlanEditorResult(session=session, approved_plan=None, safe_metadata=_safe_metadata(session, approved=False))

    def apply_edits(self, session: K2PlanEditorSession, edit_request: K2PlanEditRequest) -> K2PlanEditorResult:
        if session.status != "editing":
            raise K2PlanEditorError("K2 edits require an editing session")
        if not edit_request.patches:
            raise K2PlanEditorError("K2 edit request must include at least one patch")
        requested_mode = edit_request.requested_render_mode or session.render_mode
        requested_template_id = edit_request.template_id if edit_request.template_id is not None else session.template_id
        _validate_render_mode(render_mode=requested_mode, template_id=requested_template_id)
        by_id = {slide.slide_id: slide for slide in session.slides}
        changed_ids: list[str] = []
        for patch in edit_request.patches:
            if patch.slide_id not in by_id:
                raise K2PlanEditorError(f"unknown K2 slide_id: {patch.slide_id}")
            by_id[patch.slide_id] = _apply_patch(by_id[patch.slide_id], patch, requested_mode)
            changed_ids.append(patch.slide_id)
        slides = tuple(by_id[slide.slide_id] for slide in session.slides)
        next_sequence = len(session.events) + 1
        events = session.events + (
            _event(
                sequence=next_sequence,
                event_type="k2.plan_editor.edit.requested",
                session_id=session.session_id,
                version=session.version + 1,
                payload={
                    "patch_count": len(edit_request.patches),
                    "changed_slide_ids": tuple(changed_ids),
                    "change_summary_digest": _digest(edit_request.change_summary),
                    "retry_of_task_id": edit_request.retry_of_task_id or session.retry_of_task_id,
                },
            ),
            _event(
                sequence=next_sequence + 1,
                event_type="k2.plan_editor.slide.updated",
                session_id=session.session_id,
                version=session.version + 1,
                payload={"changed_slide_ids": tuple(changed_ids)},
            ),
        )
        if requested_mode != session.render_mode or requested_template_id != session.template_id:
            events = events + (
                _event(
                    sequence=len(events) + 1,
                    event_type="k2.plan_editor.render_mode.updated",
                    session_id=session.session_id,
                    version=session.version + 1,
                    payload={"render_mode": requested_mode, "template_id": requested_template_id},
                ),
            )
        updated = replace(
            session,
            version=session.version + 1,
            slides=slides,
            render_mode=requested_mode,
            template_id=requested_template_id,
            events=events,
            retry_of_task_id=edit_request.retry_of_task_id or session.retry_of_task_id,
        )
        _validate_session(updated)
        return K2PlanEditorResult(session=updated, approved_plan=None, safe_metadata=_safe_metadata(updated, approved=False))

    def request_approval(self, session: K2PlanEditorSession, *, operator_user_id: str = "user_local_default") -> K2PlanEditorResult:
        if session.status != "editing":
            raise K2PlanEditorError("K2 approval can only be requested from editing state")
        _validate_session(session)
        event = _event(
            sequence=len(session.events) + 1,
            event_type="k2.plan_editor.approval.requested",
            session_id=session.session_id,
            version=session.version,
            payload={"operator_user_id": _safe_short_text(operator_user_id, 80), "slide_count": len(session.slides)},
        )
        pending = replace(session, status="approval_requested", events=session.events + (event,))
        return K2PlanEditorResult(session=pending, approved_plan=None, safe_metadata=_safe_metadata(pending, approved=False))

    def approve(self, session: K2PlanEditorSession, *, operator_user_id: str = "user_local_default") -> K2PlanEditorResult:
        if session.status not in {"editing", "approval_requested"}:
            raise K2PlanEditorError("K2 session is not approvable")
        _validate_session(session)
        approved_event = _event(
            sequence=len(session.events) + 1,
            event_type="k2.plan_editor.approved",
            session_id=session.session_id,
            version=session.version,
            payload={"operator_user_id": _safe_short_text(operator_user_id, 80), "render_mode": session.render_mode},
        )
        approved_session = replace(session, status="approved", events=session.events + (approved_event,))
        approved_plan = self.to_presentation_plan(approved_session)
        return K2PlanEditorResult(
            session=approved_session,
            approved_plan=approved_plan,
            safe_metadata=_safe_metadata(approved_session, approved=True),
        )

    def to_presentation_plan(self, session: K2PlanEditorSession) -> PresentationPlan:
        if session.status != "approved":
            raise K2PlanEditorError("K2 session must be approved before conversion to PresentationPlan")
        _validate_session(session)
        slides = tuple(_planned_slide_from_editable(slide) for slide in session.slides)
        return PresentationPlan(
            deck_title=session.deck_title,
            deck_goal=session.deck_goal,
            audience=session.audience,
            tone=session.tone,
            target_slide_count=len(slides),
            story_arc=tuple(slide.story_arc_stage for slide in slides),
            slides=slides,
        )


def build_k2_capabilities_report() -> dict[str, object]:
    return {
        "mode": "k2-plan-editor-product-workflow",
        "checkpoint": K2_CHECKPOINT,
        "schema_version": K2_SCHEMA_VERSION,
        "plan_editor_workflow_supported": True,
        "editable_outline_supported": True,
        "slide_intent_editing_supported": True,
        "evidence_link_editing_supported": True,
        "visual_intent_editing_supported": True,
        "render_mode_controls_supported": True,
        "approval_gate_supported": True,
        "diff_retry_workflow_supported": True,
        "task_event_visibility_supported": True,
        "clear_failure_states_supported": True,
        "api_endpoint_added_by_k2": False,
        "db_schema_migration_added_by_k2": False,
        "frontend_runtime_changed_by_k2": False,
        "dependency_versions_changed_by_k2": False,
        "dockerfiles_changed_by_k2": False,
        "visual_qa_runtime_added_by_k2": False,
        "kimi_level_claimed_by_k2": False,
        "whole_project_kimi_level_supported": False,
    }


def _editable_slide_from_plan_slide(
    slide: PlannedSlide,
    *,
    evidence_links: tuple[K2EvidenceLink, ...],
    render_mode: str,
) -> K2EditableSlide:
    return K2EditableSlide(
        slide_id=slide.slide_id,
        slide_type=slide.slide_type.value,
        story_arc_stage=slide.story_arc_stage.value,
        title=slide.title,
        bullets=slide.bullets,
        slide_intent=_default_slide_intent(slide),
        evidence_links=evidence_links,
        visual_intent=slide.visual_intent.value,
        layout_hint=slide.layout_hint,
        render_mode=render_mode,
        source_notes=tuple(str(note) for note in slide.source_notes),
    )


def _planned_slide_from_editable(slide: K2EditableSlide) -> PlannedSlide:
    return PlannedSlide(
        slide_id=slide.slide_id,
        slide_type=SlideType(slide.slide_type),
        story_arc_stage=StoryArcStage(slide.story_arc_stage),
        title=slide.title,
        bullets=slide.bullets,
        speaker_notes=f"K2 plan editor intent: {slide.slide_intent}",
        layout_hint=slide.layout_hint,
        visual_intent=VisualIntent(slide.visual_intent),
        source_notes=slide.source_notes + tuple(link.source_id for link in slide.evidence_links),
    )


def _apply_patch(slide: K2EditableSlide, patch: K2SlidePatch, render_mode: str) -> K2EditableSlide:
    title = _safe_short_text(patch.title, 160) if patch.title is not None else slide.title
    bullets = tuple(_safe_short_text(bullet, 180) for bullet in patch.bullets) if patch.bullets is not None else slide.bullets
    slide_intent = _safe_short_text(patch.slide_intent, 240) if patch.slide_intent is not None else slide.slide_intent
    evidence_links = patch.evidence_links if patch.evidence_links is not None else slide.evidence_links
    visual_intent = patch.visual_intent if patch.visual_intent is not None else slide.visual_intent
    layout_hint = _safe_short_text(patch.layout_hint, 80) if patch.layout_hint is not None else slide.layout_hint
    source_notes = tuple(_safe_short_text(note, 120) for note in patch.source_notes) if patch.source_notes is not None else slide.source_notes
    if patch.render_mode is not None:
        render_mode = patch.render_mode
    _validate_visual_intent(visual_intent)
    _validate_render_mode(render_mode=render_mode, template_id="local_template" if render_mode == "template" else None)
    if not title:
        raise K2PlanEditorError("K2 slide title cannot be empty")
    if not bullets:
        raise K2PlanEditorError("K2 slide bullets cannot be empty")
    return replace(
        slide,
        title=title,
        bullets=bullets,
        slide_intent=slide_intent,
        evidence_links=evidence_links,
        visual_intent=visual_intent,
        layout_hint=layout_hint,
        render_mode=render_mode,
        source_notes=source_notes,
    )


def _validate_session(session: K2PlanEditorSession) -> None:
    if not session.slides:
        raise K2PlanEditorError("K2 editor session requires at least one slide")
    _validate_render_mode(render_mode=session.render_mode, template_id=session.template_id)
    for slide in session.slides:
        if not slide.title.strip():
            raise K2PlanEditorError(f"K2 slide {slide.slide_id} has empty title")
        if not slide.bullets:
            raise K2PlanEditorError(f"K2 slide {slide.slide_id} has no bullets")
        _validate_visual_intent(slide.visual_intent)
    _assert_events_safe(session.events)


def _validate_render_mode(*, render_mode: str, template_id: str | None) -> None:
    if render_mode not in _ALLOWED_RENDER_MODES:
        raise K2PlanEditorError(f"unsupported K2 render_mode: {render_mode}")
    if render_mode == "template" and not template_id:
        raise K2PlanEditorError("K2 template render mode requires explicit local template_id")


def _validate_visual_intent(value: str) -> None:
    try:
        VisualIntent(value)
    except ValueError as exc:
        raise K2PlanEditorError(f"unsupported K2 visual_intent: {value}") from exc


def _default_slide_intent(slide: PlannedSlide) -> str:
    return f"Clarify the {slide.story_arc_stage.value} role for this {slide.slide_type.value} slide."


def _event(*, sequence: int, event_type: str, session_id: str, version: int, payload: dict[str, object]) -> K2PlanEditorEvent:
    if event_type not in _ALLOWED_EVENT_TYPES:
        raise K2PlanEditorError(f"unsupported K2 event type: {event_type}")
    safe_payload = {"session_id": session_id, "version": version, **payload}
    _assert_json_safe(safe_payload)
    return K2PlanEditorEvent(event_type=event_type, sequence=sequence, payload=safe_payload)


def _safe_metadata(session: K2PlanEditorSession, *, approved: bool) -> dict[str, object]:
    metadata = {
        **build_k2_capabilities_report(),
        "session_id": session.session_id,
        "version": session.version,
        "status": session.status,
        "approved_plan_present": approved,
        "base_plan_digest": session.base_plan_digest,
        "slide_count": len(session.slides),
        "render_mode": session.render_mode,
        "template_id": session.template_id,
        "event_count": len(session.events),
        "event_types": tuple(event.event_type for event in session.events),
        "append_only_event_stream": True,
        "approval_required_before_generation": True,
        "raw_source_text_stored": False,
        "raw_prompt_stored": False,
        "raw_sensitive_values_stored": False,
    }
    _assert_json_safe(metadata)
    return metadata


def _assert_events_safe(events: tuple[K2PlanEditorEvent, ...]) -> None:
    expected = tuple(range(1, len(events) + 1))
    actual = tuple(event.sequence for event in events)
    if actual != expected:
        raise K2PlanEditorError(f"K2 event stream is not append-only sequential: {actual}")
    for event in events:
        _assert_json_safe(event.payload)


def _assert_json_safe(payload: dict[str, object]) -> None:
    def iter_values(value: object):
        if isinstance(value, dict):
            for item in value.values():
                yield from iter_values(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                yield from iter_values(item)
        elif isinstance(value, str):
            yield value.lower()

    for value in iter_values(payload):
        for forbidden in _FORBIDDEN_SAFE_TEXT:
            if forbidden in value:
                raise K2PlanEditorError("K2 safe payload contains forbidden secret-like value")


def _plan_digest(plan: PresentationPlan) -> str:
    serialized = json.dumps(
        {
            "deck_title": plan.deck_title,
            "deck_goal": plan.deck_goal,
            "audience": plan.audience,
            "tone": plan.tone,
            "slides": [
                {"slide_id": slide.slide_id, "title": slide.title, "bullets": list(slide.bullets)}
                for slide in plan.slides
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return _digest(serialized)


def _digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _safe_short_text(value: str | None, max_length: int) -> str:
    if value is None:
        return ""
    cleaned = " ".join(str(value).replace("\n", " ").split())
    return cleaned[:max_length]
