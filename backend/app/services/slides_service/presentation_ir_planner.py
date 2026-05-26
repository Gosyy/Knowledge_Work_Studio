from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from backend.app.services.slides_service.offline_evidence_index import (
    EvidenceSearchResult,
    OfflineEvidenceIndex,
)
from backend.app.services.slides_service.presentation_ir import (
    PRESENTATION_IR_SCHEMA_VERSION,
    require_presentation_ir_payload,
)

PRESENTATION_IR_PLANNER_SCHEMA_VERSION = "presentation_ir_planner.v1"

PlannerStatus = Literal["ready", "degraded", "blocked"]


@dataclass(frozen=True)
class PresentationIRPlannerRequest:
    presentation_id: str
    title: str
    objective: str
    audience: str = "general"
    language: str = "ru"
    slide_count: int = 6
    scenario: str = "report"
    tone: str = "professional"
    template_id: str = "business_clean"
    require_evidence: bool = True


@dataclass(frozen=True)
class PresentationIREvidenceBinding:
    evidence_id: str
    source_id: str
    provenance_ref: str
    section_id: str | None
    section_label: str | None
    score: float
    matched_terms: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_terms"] = list(self.matched_terms)
        return payload


@dataclass(frozen=True)
class PresentationIRPlannerResult:
    schema_version: str
    status: PlannerStatus
    presentation_id: str
    presentation_ir: dict[str, Any] | None
    evidence_bindings: tuple[PresentationIREvidenceBinding, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "presentation_id": self.presentation_id,
            "presentation_ir": self.presentation_ir,
            "evidence_bindings": [binding.as_dict() for binding in self.evidence_bindings],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


class PresentationIRPlannerFoundation:
    """Build a deterministic PresentationIR draft from offline local evidence.

    KR-7F.1 is a planner foundation, not the final GigaChat planning runtime.
    It consumes the KR-7E offline evidence index, emits a validated
    PresentationIR draft, and fails closed when evidence is required but absent.
    It does not call LLMs, embeddings, web research, render/export, visual QA,
    quality scoring, or UI runtime code.
    """

    def plan_from_evidence(
        self,
        request: PresentationIRPlannerRequest,
        evidence_index: OfflineEvidenceIndex,
    ) -> PresentationIRPlannerResult:
        normalized_slide_count = _normalize_slide_count(request.slide_count)
        if request.require_evidence and not evidence_index.records:
            return PresentationIRPlannerResult(
                schema_version=PRESENTATION_IR_PLANNER_SCHEMA_VERSION,
                status="blocked",
                presentation_id=request.presentation_id,
                presentation_ir=None,
                warnings=("evidence_required_but_index_empty",),
                errors=("Cannot build source-backed PresentationIR without offline evidence records.",),
            )

        query = " ".join(part for part in (request.title, request.objective) if part).strip() or request.presentation_id
        search_results = evidence_index.search(query, limit=max(1, normalized_slide_count * 2))
        bindings = tuple(_binding_from_search_result(result) for result in search_results)
        status: PlannerStatus = "ready" if bindings else "degraded"
        warnings: list[str] = []
        if not bindings:
            warnings.append("prompt_only_degraded_planner_output_without_source_evidence")
        if normalized_slide_count != request.slide_count:
            warnings.append("slide_count_normalized_to_supported_range")

        presentation_ir = _build_presentation_ir(
            request=request,
            slide_count=normalized_slide_count,
            evidence_index=evidence_index,
            bindings=bindings,
            status=status,
        )
        return PresentationIRPlannerResult(
            schema_version=PRESENTATION_IR_PLANNER_SCHEMA_VERSION,
            status=status,
            presentation_id=request.presentation_id,
            presentation_ir=presentation_ir,
            evidence_bindings=bindings,
            warnings=tuple(warnings),
        )


def _build_presentation_ir(
    *,
    request: PresentationIRPlannerRequest,
    slide_count: int,
    evidence_index: OfflineEvidenceIndex,
    bindings: tuple[PresentationIREvidenceBinding, ...],
    status: PlannerStatus,
) -> dict[str, Any]:
    slides: list[dict[str, Any]] = []
    for slide_number in range(1, slide_count + 1):
        role = _slide_role_for_position(slide_number, slide_count)
        slide_bindings = _bindings_for_slide(bindings, slide_number=slide_number, slide_count=slide_count)
        slides.append(
            {
                "slide_id": f"s{slide_number:03d}",
                "slide_number": slide_number,
                "role": role,
                "title": _slide_title(request=request, role=role, slide_number=slide_number),
                "takeaway": _slide_takeaway(request=request, role=role, bindings=slide_bindings),
                "evidence": [binding.as_dict() for binding in slide_bindings],
                "blocks": _slide_blocks(slide_id=f"s{slide_number:03d}", role=role, request=request, bindings=slide_bindings),
                "visual_plan": _visual_plan_for_role(role, has_evidence=bool(slide_bindings)),
                "speaker_notes": _speaker_notes_for_role(role, slide_bindings),
            }
        )

    payload: dict[str, Any] = {
        "schema_version": PRESENTATION_IR_SCHEMA_VERSION,
        "deck": {
            "presentation_id": request.presentation_id,
            "title": request.title,
            "objective": request.objective,
            "audience": request.audience,
            "tone": request.tone,
            "scenario": request.scenario,
            "language": request.language,
            "slide_count": slide_count,
            "planner_schema_version": PRESENTATION_IR_PLANNER_SCHEMA_VERSION,
            "planner_status": status,
        },
        "theme": {
            "template_id": request.template_id,
            "brand_source": "none",
            "font_family": "Aptos",
            "color_tokens": {},
        },
        "sources": _presentation_ir_sources(evidence_index),
        "assets": [],
        "slides": slides,
        "quality_contract": {
            "no_fake_charts": True,
            "no_generated_images": True,
            "source_images_only": True,
            "native_editable_components": True,
            "planner_schema_version": PRESENTATION_IR_PLANNER_SCHEMA_VERSION,
            "planner_status": status,
            "requires_source_evidence": request.require_evidence,
            "evidence_records_indexed": len(evidence_index.records),
            "fallback_is_degraded_and_explicit": status == "degraded",
        },
    }
    return require_presentation_ir_payload(payload)


def _presentation_ir_sources(evidence_index: OfflineEvidenceIndex) -> list[dict[str, Any]]:
    by_source: dict[str, dict[str, Any]] = {}
    for record in evidence_index.records:
        by_source.setdefault(
            record.source_id,
            {
                "source_id": record.source_id,
                "source_type": "document",
                "role": "evidence",
                "title": record.source_id,
                "file_type": record.source_kind,
                "mime_type": None,
                "checksum_sha256": None,
                "size_bytes": None,
                "extraction_status": "ready",
                "source_file_id": None,
                "source_document_id": record.source_id,
                "source_presentation_id": None,
                "provenance_ref": record.provenance_ref,
            },
        )
    for unsupported in evidence_index.unsupported_sources:
        source_id = str(unsupported.get("source_id") or "unsupported_source")
        by_source.setdefault(
            source_id,
            {
                "source_id": source_id,
                "source_type": "document",
                "role": "evidence",
                "title": source_id,
                "file_type": unsupported.get("source_kind"),
                "mime_type": None,
                "checksum_sha256": None,
                "size_bytes": None,
                "extraction_status": "unsupported",
                "source_file_id": None,
                "source_document_id": source_id,
                "source_presentation_id": None,
                "provenance_ref": None,
            },
        )
    return list(by_source.values())


def _slide_blocks(
    *,
    slide_id: str,
    role: str,
    request: PresentationIRPlannerRequest,
    bindings: tuple[PresentationIREvidenceBinding, ...],
) -> list[dict[str, Any]]:
    if role == "cover":
        return [
            {
                "block_id": f"{slide_id}_title",
                "type": "text",
                "semantic_role": "main_claim",
                "content": {"text": request.title, "subtitle": request.objective},
                "data_binding": None,
                "source_refs": [binding.evidence_id for binding in bindings],
            }
        ]
    items = [
        {
            "text": _binding_statement(binding),
            "evidence_id": binding.evidence_id,
            "provenance_ref": binding.provenance_ref,
        }
        for binding in bindings
    ]
    if not items:
        items = [{"text": "Source evidence is not attached to this planner draft.", "evidence_id": None, "provenance_ref": None}]
    return [
        {
            "block_id": f"{slide_id}_evidence_bullets",
            "type": "bullets",
            "semantic_role": "supporting_evidence" if bindings else "planner_gap",
            "content": {"items": items},
            "data_binding": None,
            "source_refs": [binding.evidence_id for binding in bindings],
        }
    ]


def _visual_plan_for_role(role: str, *, has_evidence: bool) -> dict[str, Any]:
    layout_by_role = {
        "cover": "cover",
        "executive_summary": "editorial",
        "insight": "split",
        "data": "dashboard",
        "roadmap": "roadmap",
        "decision": "matrix",
        "closing": "minimal",
    }
    return {
        "layout_family": layout_by_role.get(role, "editorial"),
        "density": "medium" if has_evidence else "low",
        "requires_image": False,
        "requires_chart": False,
        "requires_diagram": role in {"roadmap", "decision"},
        "allowed_without_data": role not in {"data"} or has_evidence,
    }


def _slide_role_for_position(slide_number: int, slide_count: int) -> str:
    if slide_number == 1:
        return "cover"
    if slide_number == slide_count:
        return "closing"
    sequence = ["executive_summary", "insight", "data", "roadmap", "decision"]
    return sequence[(slide_number - 2) % len(sequence)]


def _slide_title(*, request: PresentationIRPlannerRequest, role: str, slide_number: int) -> str:
    role_titles = {
        "cover": request.title,
        "executive_summary": "Executive summary",
        "insight": "Source-backed insight",
        "data": "Evidence and data points",
        "roadmap": "Recommended roadmap",
        "decision": "Decision considerations",
        "closing": "Next steps",
    }
    return role_titles.get(role, f"Section {slide_number}")


def _slide_takeaway(
    *,
    request: PresentationIRPlannerRequest,
    role: str,
    bindings: tuple[PresentationIREvidenceBinding, ...],
) -> str:
    if role == "cover":
        return request.objective
    if bindings:
        return f"This slide is grounded in {len(bindings)} local evidence fragment(s)."
    return "Evidence is not attached; this planner draft is degraded and must be reviewed."


def _speaker_notes_for_role(role: str, bindings: tuple[PresentationIREvidenceBinding, ...]) -> str:
    if bindings:
        refs = ", ".join(binding.provenance_ref for binding in bindings)
        return f"Evidence refs: {refs}"
    return f"Planner note for {role}: attach source evidence before claiming support."


def _bindings_for_slide(
    bindings: tuple[PresentationIREvidenceBinding, ...],
    *,
    slide_number: int,
    slide_count: int,
) -> tuple[PresentationIREvidenceBinding, ...]:
    if not bindings:
        return ()
    if slide_number == 1:
        return bindings[:1]
    bucket = slide_number - 2
    bucket_count = max(1, slide_count - 2)
    return tuple(binding for index, binding in enumerate(bindings) if index % bucket_count == bucket)[:3]


def _binding_from_search_result(result: EvidenceSearchResult) -> PresentationIREvidenceBinding:
    return PresentationIREvidenceBinding(
        evidence_id=result.evidence_id,
        source_id=result.source_id,
        provenance_ref=result.provenance_ref,
        section_id=result.section_id,
        section_label=result.section_label,
        score=result.score,
        matched_terms=tuple(result.matched_terms),
    )


def _binding_statement(binding: PresentationIREvidenceBinding) -> str:
    section = binding.section_label or binding.section_id or binding.source_id
    return f"{section}: evidence score {binding.score:.2f}"


def _normalize_slide_count(slide_count: int) -> int:
    return min(20, max(1, int(slide_count)))


__all__ = [
    "PRESENTATION_IR_PLANNER_SCHEMA_VERSION",
    "PresentationIREvidenceBinding",
    "PresentationIRPlannerFoundation",
    "PresentationIRPlannerRequest",
    "PresentationIRPlannerResult",
]
