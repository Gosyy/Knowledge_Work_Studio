from __future__ import annotations

import re
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
from backend.app.services.slides_service.visual_grammar import (
    VISUAL_GRAMMAR_SCHEMA_VERSION,
    PresentationVisualGrammarLibrary,
    VisualGrammarValidationResult,
)

PRESENTATION_IR_PLANNER_SCHEMA_VERSION = "presentation_ir_planner.v1"
PRESENTATION_IR_OUTLINE_SCHEMA_VERSION = "presentation_ir_outline.v1"
PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION = "presentation_ir_planner_snapshot.v1"
PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION = "presentation_ir_visual_grammar_binding.v1"

PlannerStatus = Literal["ready", "degraded", "blocked"]
SlideSupportStatus = Literal["supported", "weak", "unsupported"]

_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{2,}", flags=re.UNICODE)
_STOPWORDS = {
    "and",
    "the",
    "for",
    "of",
    "to",
    "in",
    "with",
    "show",
    "source",
    "backed",
    "general",
    "executive",
    "summary",
    "points",
}


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
    required_sections: tuple[str, ...] = ()
    min_outline_coverage_ratio: float = 0.6


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
class PresentationIRSlideOutline:
    schema_version: str
    slide_id: str
    slide_number: int
    role: str
    title: str
    intent_query: str
    expected_terms: tuple[str, ...]
    support_status: SlideSupportStatus
    coverage_ratio: float
    evidence_bindings: tuple[PresentationIREvidenceBinding, ...] = ()
    missing_terms: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "slide_id": self.slide_id,
            "slide_number": self.slide_number,
            "role": self.role,
            "title": self.title,
            "intent_query": self.intent_query,
            "expected_terms": list(self.expected_terms),
            "support_status": self.support_status,
            "coverage_ratio": self.coverage_ratio,
            "evidence_bindings": [binding.as_dict() for binding in self.evidence_bindings],
            "missing_terms": list(self.missing_terms),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class PresentationIRPlannerResult:
    schema_version: str
    status: PlannerStatus
    presentation_id: str
    presentation_ir: dict[str, Any] | None
    evidence_bindings: tuple[PresentationIREvidenceBinding, ...] = ()
    slide_outlines: tuple[PresentationIRSlideOutline, ...] = ()
    coverage_summary: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "presentation_id": self.presentation_id,
            "presentation_ir": self.presentation_ir,
            "evidence_bindings": [binding.as_dict() for binding in self.evidence_bindings],
            "slide_outlines": [outline.as_dict() for outline in self.slide_outlines],
            "coverage_summary": dict(self.coverage_summary),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


class PresentationIRPlannerFoundation:
    """Build a deterministic PresentationIR draft from offline local evidence.

    KR-7F.2 hardens the KR-7F.1 foundation by planning slide outlines
    against KR-7E local evidence sections before constructing slides. It is
    still not the final GigaChat planning runtime. It binds KR-7G visual grammar blocks into eligible PresentationIR slides,
    KR-7G.2 bind visual grammar blocks into PresentationIR planner output.
    This does not call LLMs, embeddings, web research, PostgreSQL FTS
    runtime, render/export, visual QA, quality scoring, or UI runtime code.
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

        outlines = _build_slide_outlines(
            request=request,
            slide_count=normalized_slide_count,
            evidence_index=evidence_index,
        )
        bindings = _unique_bindings(outline.evidence_bindings for outline in outlines)
        coverage_summary = _coverage_summary(outlines=outlines, request=request)
        status = _planner_status(request=request, outlines=outlines, bindings=bindings, coverage_summary=coverage_summary)
        warnings = _planner_warnings(
            request=request,
            normalized_slide_count=normalized_slide_count,
            status=status,
            outlines=outlines,
            coverage_summary=coverage_summary,
        )

        presentation_ir = _build_presentation_ir(
            request=request,
            slide_count=normalized_slide_count,
            evidence_index=evidence_index,
            outlines=outlines,
            bindings=bindings,
            status=status,
            coverage_summary=coverage_summary,
        )
        return PresentationIRPlannerResult(
            schema_version=PRESENTATION_IR_PLANNER_SCHEMA_VERSION,
            status=status,
            presentation_id=request.presentation_id,
            presentation_ir=presentation_ir,
            evidence_bindings=bindings,
            slide_outlines=outlines,
            coverage_summary=coverage_summary,
            warnings=warnings,
        )


def presentation_ir_planner_snapshot_metadata(result: PresentationIRPlannerResult) -> dict[str, Any]:
    return {
        "schema_version": PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION,
        "planner_schema_version": result.schema_version,
        "outline_schema_version": PRESENTATION_IR_OUTLINE_SCHEMA_VERSION,
        "status": result.status,
        "presentation_id": result.presentation_id,
        "has_presentation_ir": result.presentation_ir is not None,
        "evidence_binding_count": len(result.evidence_bindings),
        "slide_outline_count": len(result.slide_outlines),
        "coverage_summary": dict(result.coverage_summary),
        "warnings": list(result.warnings),
        "errors": list(result.errors),
    }


def presentation_ir_planner_snapshot_metadata_from_ir(presentation_ir: dict[str, Any]) -> dict[str, Any] | None:
    planner_snapshot = presentation_ir.get("planner_snapshot")
    if not isinstance(planner_snapshot, dict):
        return None
    if planner_snapshot.get("schema_version") != PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION:
        return None
    safe_snapshot = {
        "schema_version": PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION,
        "planner_schema_version": str(planner_snapshot.get("planner_schema_version") or PRESENTATION_IR_PLANNER_SCHEMA_VERSION),
        "outline_schema_version": str(planner_snapshot.get("outline_schema_version") or PRESENTATION_IR_OUTLINE_SCHEMA_VERSION),
        "status": str(planner_snapshot.get("status") or "degraded"),
        "presentation_id": str(planner_snapshot.get("presentation_id") or presentation_ir.get("deck", {}).get("presentation_id") or ""),
        "has_presentation_ir": bool(planner_snapshot.get("has_presentation_ir", True)),
        "evidence_binding_count": int(planner_snapshot.get("evidence_binding_count") or 0),
        "slide_outline_count": int(planner_snapshot.get("slide_outline_count") or 0),
        "coverage_summary": dict(planner_snapshot.get("coverage_summary") or {}),
        "warnings": [str(item) for item in planner_snapshot.get("warnings", [])],
        "errors": [str(item) for item in planner_snapshot.get("errors", [])],
    }
    return safe_snapshot


def require_persistable_presentation_ir_planner_result(result: PresentationIRPlannerResult) -> dict[str, Any]:
    if result.status == "blocked" or result.presentation_ir is None:
        raise ValueError("Blocked PresentationIR planner results cannot be persisted as PresentationIR snapshots.")
    payload = require_presentation_ir_payload(dict(result.presentation_ir))
    payload["planner_snapshot"] = presentation_ir_planner_snapshot_metadata(result)
    payload.setdefault("quality_contract", {})["planner_snapshot_schema_version"] = PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION
    payload.setdefault("quality_contract", {})["planner_snapshot_persisted"] = True
    payload.setdefault("deck", {})["planner_snapshot_schema_version"] = PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION
    return require_presentation_ir_payload(payload)


# Backward compatible alias for earlier KR-7F.1 wording used by some checks.
# The implementation now builds evidence-aware slide outlines first.
PresentationIRPlannerFoundation.plan_from_evidence.__doc__ = """Plan PresentationIR from offline evidence without LLM calls."""


def _build_presentation_ir(
    *,
    request: PresentationIRPlannerRequest,
    slide_count: int,
    evidence_index: OfflineEvidenceIndex,
    outlines: tuple[PresentationIRSlideOutline, ...],
    bindings: tuple[PresentationIREvidenceBinding, ...],
    status: PlannerStatus,
    coverage_summary: dict[str, Any],
) -> dict[str, Any]:
    visual_grammar_library = PresentationVisualGrammarLibrary()
    slides: list[dict[str, Any]] = []
    visual_grammar_results: list[VisualGrammarValidationResult] = []
    for outline in outlines:
        blocks = _slide_blocks(
            slide_id=outline.slide_id,
            role=outline.role,
            request=request,
            outline=outline,
            visual_grammar_library=visual_grammar_library,
        )
        visual_grammar_results.extend(visual_grammar_library.validate_presentation_ir_blocks({"slides": [{"blocks": blocks}]}))
        slides.append(
            {
                "slide_id": outline.slide_id,
                "slide_number": outline.slide_number,
                "role": outline.role,
                "title": outline.title,
                "takeaway": _slide_takeaway(request=request, outline=outline),
                "evidence": [binding.as_dict() for binding in outline.evidence_bindings],
                "outline": outline.as_dict(),
                "blocks": blocks,
                "visual_plan": _visual_plan_for_role(outline.role, has_evidence=bool(outline.evidence_bindings)),
                "speaker_notes": _speaker_notes_for_outline(outline),
            }
        )
    visual_grammar_summary = _visual_grammar_summary(results=tuple(visual_grammar_results), slides=slides)

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
            "outline_schema_version": PRESENTATION_IR_OUTLINE_SCHEMA_VERSION,
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
            "outline_schema_version": PRESENTATION_IR_OUTLINE_SCHEMA_VERSION,
            "planner_status": status,
            "requires_source_evidence": request.require_evidence,
            "evidence_records_indexed": len(evidence_index.records),
            "fallback_is_degraded_and_explicit": status == "degraded",
            "evidence_aware_outline_planning": True,
            "outline_coverage_ratio": coverage_summary["outline_coverage_ratio"],
            "supported_slide_count": coverage_summary["supported_slide_count"],
            "unsupported_slide_count": coverage_summary["unsupported_slide_count"],
            "visual_grammar_schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
            "visual_grammar_binding_schema_version": PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
            "visual_grammar_bound_blocks": visual_grammar_summary["bound_block_count"],
            "visual_grammar_blocked_blocks": visual_grammar_summary["blocked_block_count"],
            "visual_grammar_binding_status": visual_grammar_summary["status"],
        },
    }
    return require_presentation_ir_payload(payload)


def _build_slide_outlines(
    *,
    request: PresentationIRPlannerRequest,
    slide_count: int,
    evidence_index: OfflineEvidenceIndex,
) -> tuple[PresentationIRSlideOutline, ...]:
    outlines: list[PresentationIRSlideOutline] = []
    for slide_number in range(1, slide_count + 1):
        role = _slide_role_for_position(slide_number, slide_count, required_sections=request.required_sections)
        title = _slide_title(request=request, role=role, slide_number=slide_number)
        query = _intent_query(request=request, role=role, title=title)
        expected_terms = tuple(dict.fromkeys(_tokenize(query)))
        results = evidence_index.search(query, limit=3)
        bindings = tuple(_binding_from_search_result(result) for result in results)
        matched_terms = set(term for binding in bindings for term in binding.matched_terms)
        missing_terms = tuple(term for term in expected_terms if term not in matched_terms)
        coverage_ratio = round((len(expected_terms) - len(missing_terms)) / max(1, len(expected_terms)), 6)
        support_status = _support_status(bindings=bindings, coverage_ratio=coverage_ratio)
        warnings = _outline_warnings(
            role=role,
            bindings=bindings,
            missing_terms=missing_terms,
            support_status=support_status,
        )
        outlines.append(
            PresentationIRSlideOutline(
                schema_version=PRESENTATION_IR_OUTLINE_SCHEMA_VERSION,
                slide_id=f"s{slide_number:03d}",
                slide_number=slide_number,
                role=role,
                title=title,
                intent_query=query,
                expected_terms=expected_terms,
                support_status=support_status,
                coverage_ratio=coverage_ratio,
                evidence_bindings=bindings,
                missing_terms=missing_terms,
                warnings=warnings,
            )
        )
    return tuple(outlines)


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
    outline: PresentationIRSlideOutline,
    visual_grammar_library: PresentationVisualGrammarLibrary,
) -> list[dict[str, Any]]:
    visual_block = _visual_grammar_block(
        slide_id=slide_id,
        role=role,
        request=request,
        outline=outline,
    )
    if visual_block is not None:
        validation = visual_grammar_library.validate_block(visual_block)
        visual_block["visual_grammar_binding"] = _visual_grammar_binding_payload(
            block_type=str(visual_block.get("type") or ""),
            validation=validation,
        )
        return [visual_block]

    return [
        {
            "block_id": f"{slide_id}_visual_grammar_gap",
            "type": "bullets",
            "semantic_role": "planner_gap",
            "content": {
                "items": [
                    {
                        "text": "Visual grammar block is not bound because local source evidence is missing or unsupported.",
                        "evidence_id": None,
                        "provenance_ref": None,
                        "missing_terms": list(outline.missing_terms),
                    }
                ]
            },
            "data_binding": None,
            "source_refs": [],
            "visual_grammar_binding": {
                "schema_version": PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
                "visual_grammar_schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
                "status": "blocked",
                "reason": "unsupported_outline_without_source_evidence",
                "block_type": None,
                "validation": None,
            },
        }
    ]


def _visual_grammar_block(
    *,
    slide_id: str,
    role: str,
    request: PresentationIRPlannerRequest,
    outline: PresentationIRSlideOutline,
) -> dict[str, Any] | None:
    if not outline.evidence_bindings or outline.support_status == "unsupported":
        return None
    block_type = _visual_grammar_block_type_for_role(role)
    source_refs = [binding.evidence_id for binding in outline.evidence_bindings]
    base = {
        "block_id": f"{slide_id}_{block_type}",
        "type": block_type,
        "semantic_role": _visual_grammar_semantic_role(role=role, block_type=block_type),
        "source_refs": source_refs,
        "visual_grammar_binding": {
            "schema_version": PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
            "visual_grammar_schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
            "status": "pending_validation",
            "block_type": block_type,
        },
    }
    if block_type == "executive_summary_cards":
        base["content"] = {
            "cards": [
                {
                    "title": outline.title,
                    "text": _slide_takeaway(request=request, outline=outline),
                    "evidence_id": binding.evidence_id,
                    "provenance_ref": binding.provenance_ref,
                }
                for binding in outline.evidence_bindings[:3]
            ]
        }
        base["data_binding"] = None
    elif block_type == "data_table":
        base["content"] = {
            "columns": ["Evidence", "Source", "Matched terms"],
            "rows": [
                [_binding_statement(binding), binding.source_id, ", ".join(binding.matched_terms)]
                for binding in outline.evidence_bindings[:4]
            ],
        }
        base["data_binding"] = {"source_ref": source_refs[0]}
    elif block_type == "roadmap":
        base["content"] = {
            "phases": [
                {
                    "label": f"Step {index + 1}",
                    "text": _binding_statement(binding),
                    "evidence_id": binding.evidence_id,
                }
                for index, binding in enumerate(outline.evidence_bindings[:4])
            ]
        }
        base["data_binding"] = None
    elif block_type == "decision_matrix":
        base["content"] = {
            "criteria": ["Evidence support", "Source relevance", "Operator review"],
            "options": [binding.section_label or binding.source_id for binding in outline.evidence_bindings[:3]],
            "scores": [["source-backed", f"score:{binding.score:.2f}", "required"] for binding in outline.evidence_bindings[:3]],
        }
        base["data_binding"] = None
    elif block_type == "risk_matrix":
        base["content"] = {
            "risks": [
                {
                    "label": binding.section_label or binding.source_id,
                    "likelihood": "unknown_without_numeric_model",
                    "impact": "operator_review_required",
                    "evidence_id": binding.evidence_id,
                }
                for binding in outline.evidence_bindings[:4]
            ]
        }
        base["data_binding"] = None
    else:
        base["content"] = {"cards": [{"title": outline.title, "text": _binding_statement(outline.evidence_bindings[0])}]}
        base["data_binding"] = None
    return base


def _visual_grammar_block_type_for_role(role: str) -> str:
    if role == "data":
        return "data_table"
    if role == "roadmap":
        return "roadmap"
    if role == "decision":
        return "decision_matrix"
    if role in {"risk", "risks"}:
        return "risk_matrix"
    return "executive_summary_cards"


def _visual_grammar_semantic_role(*, role: str, block_type: str) -> str:
    if block_type == "data_table":
        return "source_data_table"
    if block_type in {"roadmap", "decision_matrix", "risk_matrix"}:
        return role or block_type
    return "source_backed_summary"


def _visual_grammar_binding_payload(*, block_type: str, validation: VisualGrammarValidationResult) -> dict[str, Any]:
    return {
        "schema_version": PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
        "visual_grammar_schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
        "status": validation.status,
        "block_type": block_type,
        "validation": validation.as_dict(),
    }


def _visual_grammar_summary(*, results: tuple[VisualGrammarValidationResult, ...], slides: list[dict[str, Any]]) -> dict[str, Any]:
    bound_blocks = [
        block
        for slide in slides
        for block in slide.get("blocks", [])
        if isinstance(block, dict)
        and isinstance(block.get("visual_grammar_binding"), dict)
        and block["visual_grammar_binding"].get("block_type")
    ]
    blocked = [result for result in results if result.status != "ready"]
    explicit_gaps = [
        block
        for slide in slides
        for block in slide.get("blocks", [])
        if isinstance(block, dict)
        and isinstance(block.get("visual_grammar_binding"), dict)
        and block["visual_grammar_binding"].get("status") == "blocked"
    ]
    status = "ready" if bound_blocks and not blocked else "degraded"
    if not bound_blocks:
        status = "blocked"
    return {
        "schema_version": PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION,
        "visual_grammar_schema_version": VISUAL_GRAMMAR_SCHEMA_VERSION,
        "status": status,
        "bound_block_count": len(bound_blocks),
        "blocked_block_count": len(blocked) + len(explicit_gaps),
        "validated_block_count": len(results),
        "issue_codes": sorted({issue.code for result in blocked for issue in result.issues}),
    }


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


def _slide_role_for_position(slide_number: int, slide_count: int, *, required_sections: tuple[str, ...]) -> str:
    if slide_number == 1:
        return "cover"
    if slide_number == slide_count:
        return "closing"
    if required_sections:
        return _safe_role(required_sections[(slide_number - 2) % len(required_sections)])
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
    if role in role_titles:
        return role_titles[role]
    return role.replace("_", " ").strip().title() or f"Section {slide_number}"


def _intent_query(*, request: PresentationIRPlannerRequest, role: str, title: str) -> str:
    role_terms = {
        "cover": request.title,
        "executive_summary": request.objective,
        "insight": f"{request.objective} insight impact",
        "data": f"{request.objective} data metrics evidence",
        "roadmap": f"{request.objective} roadmap next steps",
        "decision": f"{request.objective} decision risk tradeoff",
        "closing": f"{request.objective} next steps recommendation",
    }
    return " ".join(part for part in (title, role_terms.get(role, role), request.audience) if part).strip()


def _slide_takeaway(*, request: PresentationIRPlannerRequest, outline: PresentationIRSlideOutline) -> str:
    if outline.role == "cover":
        return request.objective
    if outline.support_status == "supported":
        return f"This slide outline is grounded in {len(outline.evidence_bindings)} local evidence fragment(s)."
    if outline.support_status == "weak":
        return "This slide outline has partial local evidence and requires operator review."
    return "Evidence is not attached; this slide outline is unsupported and must be revised."


def _speaker_notes_for_outline(outline: PresentationIRSlideOutline) -> str:
    if outline.evidence_bindings:
        refs = ", ".join(binding.provenance_ref for binding in outline.evidence_bindings)
        return f"Evidence refs: {refs}"
    if outline.missing_terms:
        return f"Unsupported outline terms: {', '.join(outline.missing_terms)}"
    return f"Planner note for {outline.role}: attach source evidence before claiming support."


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
    matched = ", ".join(binding.matched_terms) if binding.matched_terms else "no matched terms"
    return f"{section}: evidence score {binding.score:.2f}; matched terms: {matched}"


def _unique_bindings(binding_groups: tuple[PresentationIREvidenceBinding, ...] | list[tuple[PresentationIREvidenceBinding, ...]] | Any) -> tuple[PresentationIREvidenceBinding, ...]:
    unique: dict[str, PresentationIREvidenceBinding] = {}
    for group in binding_groups:
        for binding in group:
            unique.setdefault(binding.evidence_id, binding)
    return tuple(unique.values())


def _coverage_summary(*, outlines: tuple[PresentationIRSlideOutline, ...], request: PresentationIRPlannerRequest) -> dict[str, Any]:
    supported = tuple(outline for outline in outlines if outline.support_status == "supported")
    weak = tuple(outline for outline in outlines if outline.support_status == "weak")
    unsupported = tuple(outline for outline in outlines if outline.support_status == "unsupported")
    ratio = round(len(supported) / max(1, len(outlines)), 6)
    return {
        "schema_version": PRESENTATION_IR_OUTLINE_SCHEMA_VERSION,
        "outline_coverage_ratio": ratio,
        "required_outline_coverage_ratio": _normalize_coverage_threshold(request.min_outline_coverage_ratio),
        "slide_count": len(outlines),
        "supported_slide_count": len(supported),
        "weak_slide_count": len(weak),
        "unsupported_slide_count": len(unsupported),
        "unsupported_slide_ids": [outline.slide_id for outline in unsupported],
        "weak_slide_ids": [outline.slide_id for outline in weak],
    }


def _planner_status(
    *,
    request: PresentationIRPlannerRequest,
    outlines: tuple[PresentationIRSlideOutline, ...],
    bindings: tuple[PresentationIREvidenceBinding, ...],
    coverage_summary: dict[str, Any],
) -> PlannerStatus:
    if not bindings:
        return "degraded"
    if coverage_summary["outline_coverage_ratio"] < coverage_summary["required_outline_coverage_ratio"]:
        return "degraded"
    if any(outline.support_status == "unsupported" for outline in outlines if outline.role not in {"cover", "closing"}):
        return "degraded"
    return "ready"


def _planner_warnings(
    *,
    request: PresentationIRPlannerRequest,
    normalized_slide_count: int,
    status: PlannerStatus,
    outlines: tuple[PresentationIRSlideOutline, ...],
    coverage_summary: dict[str, Any],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if status == "degraded":
        warnings.append("evidence_aware_outline_planner_degraded")
    if not any(outline.evidence_bindings for outline in outlines):
        warnings.append("prompt_only_degraded_planner_output_without_source_evidence")
    if normalized_slide_count != request.slide_count:
        warnings.append("slide_count_normalized_to_supported_range")
    if coverage_summary["outline_coverage_ratio"] < coverage_summary["required_outline_coverage_ratio"]:
        warnings.append("outline_coverage_below_required_threshold")
    if coverage_summary["unsupported_slide_count"]:
        warnings.append("outline_contains_unsupported_slides")
    return tuple(dict.fromkeys(warnings))


def _support_status(*, bindings: tuple[PresentationIREvidenceBinding, ...], coverage_ratio: float) -> SlideSupportStatus:
    if not bindings:
        return "unsupported"
    if coverage_ratio >= 0.4:
        return "supported"
    return "weak"


def _outline_warnings(
    *,
    role: str,
    bindings: tuple[PresentationIREvidenceBinding, ...],
    missing_terms: tuple[str, ...],
    support_status: SlideSupportStatus,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not bindings:
        warnings.append("slide_outline_without_evidence")
    if missing_terms:
        warnings.append("slide_outline_missing_expected_terms")
    if support_status == "weak":
        warnings.append("slide_outline_weak_evidence_support")
    if role == "data" and not bindings:
        warnings.append("data_slide_without_source_data")
    return tuple(warnings)


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text or "") if token.lower() not in _STOPWORDS]


def _safe_role(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value.strip().lower()).strip("_") or "section"


def _normalize_slide_count(slide_count: int) -> int:
    return min(20, max(1, int(slide_count)))


def _normalize_coverage_threshold(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


__all__ = [
    "PRESENTATION_IR_OUTLINE_SCHEMA_VERSION",
    "PRESENTATION_IR_PLANNER_SNAPSHOT_SCHEMA_VERSION",
    "PRESENTATION_IR_PLANNER_SCHEMA_VERSION",
    "PRESENTATION_IR_VISUAL_GRAMMAR_BINDING_SCHEMA_VERSION",
    "PresentationIREvidenceBinding",
    "PresentationIRPlannerFoundation",
    "PresentationIRPlannerRequest",
    "PresentationIRPlannerResult",
    "PresentationIRSlideOutline",
    "presentation_ir_planner_snapshot_metadata",
    "presentation_ir_planner_snapshot_metadata_from_ir",
    "require_persistable_presentation_ir_planner_result",
]
