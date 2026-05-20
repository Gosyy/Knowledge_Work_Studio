from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.services.slides_service.outline import PresentationPlan, build_presentation_plan
from backend.app.services.slides_service.source_grounding import (
    SlideCitation,
    SourceGroundingResult,
    build_source_grounded_plan,
)

SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION = "kr6a.slides_source_grounded.v1"


@dataclass(frozen=True)
class SlidesSourceGroundedArtifact:
    path: str
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SlidesSourceGroundingQuality:
    status: str
    checks: dict[str, bool]
    issues: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checks": dict(self.checks), "issues": list(self.issues)}


@dataclass(frozen=True)
class SlidesSourceGroundedBundle:
    schema_version: str
    status: str
    grounding: SourceGroundingResult
    artifacts: dict[str, bytes]
    quality: SlidesSourceGroundingQuality

    def artifact_names(self) -> tuple[str, ...]:
        return tuple(sorted(self.artifacts))

    def text_artifact(self, path: str) -> str:
        return self.artifacts[path].decode("utf-8")


def build_source_grounded_slides_bundle(
    *,
    source_text: str,
    source_refs: tuple[dict[str, Any], ...],
    min_slides: int = 5,
    max_slides: int = 6,
) -> SlidesSourceGroundedBundle:
    """Build a deterministic KR-6A source-grounded plan/evidence bundle.

    KR-6A intentionally validates source grounding and evidence artifacts. It
    does not claim OCR, figure extraction, unsupported table extraction, visual
    QA completion, or full presentation-quality parity.
    """
    plan = build_presentation_plan(source_text, min_slides=min_slides, max_slides=max_slides)
    grounding = build_source_grounded_plan(plan, source_text=source_text, source_refs=source_refs)
    artifacts: dict[str, bytes] = {}

    slide_plan = _slide_plan_payload(grounding.plan)
    citations = _citation_manifest_payload(grounding.citations)
    evidence = _source_evidence_manifest_payload(grounding)
    quality = validate_source_grounded_slides_bundle(grounding=grounding, source_refs=source_refs)

    artifacts["slide_plan.json"] = _json_bytes(slide_plan)
    artifacts["citation_manifest.json"] = _json_bytes(citations)
    artifacts["source_evidence_manifest.json"] = _json_bytes(evidence)
    artifacts["quality_report.json"] = _json_bytes(quality.as_dict())

    manifest_placeholder = {
        "schema_version": SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION,
        "workflow_id": "slides",
        "status": quality.status,
        "self_reference": {
            "path": "artifact_manifest.json",
            "hash_policy": "manifest file is self-referential; hash is intentionally omitted",
        },
        "artifacts": [],
    }
    artifacts["artifact_manifest.json"] = _json_bytes(manifest_placeholder)
    artifacts["artifact_manifest.json"] = _json_bytes(
        {
            "schema_version": SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION,
            "workflow_id": "slides",
            "status": quality.status,
            "self_reference": manifest_placeholder["self_reference"],
            "artifacts": [_artifact_record(path, content).as_dict() for path, content in sorted(artifacts.items())],
        }
    )

    return SlidesSourceGroundedBundle(
        schema_version=SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION,
        status=quality.status,
        grounding=grounding,
        artifacts=artifacts,
        quality=quality,
    )


def validate_source_grounded_slides_bundle(
    *,
    grounding: SourceGroundingResult,
    source_refs: tuple[dict[str, Any], ...],
) -> SlidesSourceGroundingQuality:
    slides = grounding.plan.slides
    citation_ids = {citation.citation_id for citation in grounding.citations}
    slide_citation_ids = {
        str(getattr(citation, "citation_id", ""))
        for slide in slides
        for citation in slide.citations
        if getattr(citation, "citation_id", None)
    }
    checks = {
        "source_refs_present": bool(source_refs),
        "slides_present": bool(slides),
        "citation_manifest_ready": bool(citation_ids),
        "all_slides_have_citations": bool(slides) and all(bool(slide.citations) for slide in slides),
        "all_slide_citations_in_manifest": slide_citation_ids.issubset(citation_ids),
        "source_notes_present": bool(slides) and all(bool(slide.source_notes) for slide in slides),
        "citations_have_excerpts": all(bool(citation.excerpt.strip()) for citation in grounding.citations),
        "citations_have_source_labels": all(bool(citation.source_label.strip()) for citation in grounding.citations),
        "no_unsupported_extraction_claim": True,
    }
    issues = tuple(name for name, passed in checks.items() if not passed)
    return SlidesSourceGroundingQuality(status="ready" if not issues else "not_ready", checks=checks, issues=issues)


def _slide_plan_payload(plan: PresentationPlan) -> dict[str, Any]:
    return {
        "schema_version": SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION,
        "deck_title": plan.deck_title,
        "deck_goal": plan.deck_goal,
        "audience": plan.audience,
        "target_slide_count": plan.target_slide_count,
        "slides": [
            {
                "slide_id": slide.slide_id,
                "slide_type": str(slide.slide_type.value if hasattr(slide.slide_type, "value") else slide.slide_type),
                "story_arc_stage": str(
                    slide.story_arc_stage.value if hasattr(slide.story_arc_stage, "value") else slide.story_arc_stage
                ),
                "title": slide.title,
                "bullets": list(slide.bullets),
                "citations": [getattr(citation, "as_dict", lambda: {})() for citation in slide.citations],
                "source_notes": list(slide.source_notes),
            }
            for slide in plan.slides
        ],
    }


def _citation_manifest_payload(citations: tuple[SlideCitation, ...]) -> dict[str, Any]:
    return {
        "schema_version": SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION,
        "workflow_id": "slides",
        "citation_count": len(citations),
        "citations": [citation.as_dict() for citation in citations],
    }


def _source_evidence_manifest_payload(grounding: SourceGroundingResult) -> dict[str, Any]:
    evidence_items: list[dict[str, Any]] = []
    for slide in grounding.plan.slides:
        for citation in slide.citations:
            if not isinstance(citation, SlideCitation):
                continue
            evidence_items.append(
                {
                    "slide_id": slide.slide_id,
                    "citation_id": citation.citation_id,
                    "source_kind": citation.source_kind,
                    "source_id": citation.source_id,
                    "source_label": citation.source_label,
                    "fragment_id": citation.fragment_id,
                    "excerpt": citation.excerpt,
                    "derived_content_id": citation.derived_content_id,
                }
            )
    return {
        "schema_version": SLIDES_SOURCE_GROUNDED_SCHEMA_VERSION,
        "workflow_id": "slides",
        "evidence_items": evidence_items,
    }


def _artifact_record(path: str, content: bytes) -> SlidesSourceGroundedArtifact:
    return SlidesSourceGroundedArtifact(path=path, size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest())


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def sample_source_text() -> str:
    return (
        "Revenue grew 18 percent in the enterprise segment. "
        "Customer onboarding time dropped from 12 days to 7 days. "
        "Support ticket volume decreased after the workflow automation launch. "
        "The next operating priority is evidence-backed expansion into regulated teams."
    )


def sample_source_refs() -> tuple[dict[str, Any], ...]:
    return (
        {
            "kind": "docx",
            "source_id": "operator_brief",
            "role": "primary_source",
            "source_file_id": "file_operator_brief",
            "source_document_id": "doc_operator_brief",
            "derived_content_id": "derived_operator_brief_text",
        },
        {
            "kind": "xlsx",
            "source_id": "metrics_workbook",
            "role": "supporting_metrics",
            "source_file_id": "file_metrics_workbook",
            "derived_content_id": "derived_metrics_summary",
        },
    )
