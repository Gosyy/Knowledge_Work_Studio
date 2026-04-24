from __future__ import annotations

from dataclasses import dataclass, replace
from html import escape
from typing import Any

from backend.app.services.slides_service.layouts import ShapeBox, SlideTemplate
from backend.app.services.slides_service.outline import PlannedSlide, PresentationPlan


@dataclass(frozen=True)
class SourceReference:
    kind: str
    source_id: str
    role: str
    source_file_id: str | None = None
    source_document_id: str | None = None
    source_presentation_id: str | None = None
    derived_content_id: str | None = None

    @property
    def display_label(self) -> str:
        return f"{self.kind}/{self.source_id}"


@dataclass(frozen=True)
class SourceFragment:
    fragment_id: str
    source: SourceReference
    ordinal: int
    excerpt: str


@dataclass(frozen=True)
class SlideCitation:
    citation_id: str
    source_kind: str
    source_id: str
    fragment_id: str
    source_label: str
    excerpt: str
    derived_content_id: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {
            "citation_id": self.citation_id,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "fragment_id": self.fragment_id,
            "source_label": self.source_label,
            "excerpt": self.excerpt,
        }
        if self.derived_content_id:
            payload["derived_content_id"] = self.derived_content_id
        return payload


@dataclass(frozen=True)
class SourceGroundingResult:
    plan: PresentationPlan
    citations: tuple[SlideCitation, ...]

    def as_metadata(self) -> dict[str, object]:
        return {
            "citation_count": len(self.citations),
            "citations": [citation.as_dict() for citation in self.citations],
        }


def build_source_grounded_plan(
    plan: PresentationPlan,
    *,
    source_text: str,
    source_refs: tuple[dict[str, Any], ...] = (),
) -> SourceGroundingResult:
    """Attach honest source citations to slides without inventing visual extraction.

    M14 grounding is text/outline based. It maps existing resolved sources and
    derived text fragments to slides. It does not claim OCR, figure extraction,
    or unsupported table extraction.
    """
    references = _normalize_source_refs(source_refs)
    if not references:
        return SourceGroundingResult(plan=plan, citations=())

    fragments = _build_source_fragments(source_text=source_text, references=references)
    if not fragments:
        return SourceGroundingResult(plan=plan, citations=())

    updated_slides: list[PlannedSlide] = []
    citations: list[SlideCitation] = []
    for index, slide in enumerate(plan.slides):
        fragment = fragments[index % len(fragments)]
        citation = SlideCitation(
            citation_id=f"cite_{slide.slide_id}_{fragment.fragment_id}",
            source_kind=fragment.source.kind,
            source_id=fragment.source.source_id,
            fragment_id=fragment.fragment_id,
            source_label=fragment.source.display_label,
            excerpt=fragment.excerpt,
            derived_content_id=fragment.source.derived_content_id,
        )
        citations.append(citation)
        source_notes = (
            f"Source-grounded from {citation.source_label}: {citation.excerpt}",
        )
        updated_slides.append(
            replace(
                slide,
                citations=(citation,),
                source_notes=source_notes,
            )
        )

    grounded_plan = replace(plan, slides=tuple(updated_slides))
    return SourceGroundingResult(plan=grounded_plan, citations=tuple(citations))


def render_slide_citations_xml(
    *,
    citations: tuple[SlideCitation, ...],
    template: SlideTemplate,
    slide_index: int,
) -> str:
    if not citations:
        return ""
    footer_box = ShapeBox(457200, 6400800, 8229600, 274320)
    text = " | ".join(
        f"Source: {citation.source_label} — {_clip(citation.excerpt, 72)}"
        for citation in citations[:2]
    )
    return f'''      <p:sp>
        <p:nvSpPr><p:cNvPr id="{slide_index * 1000 + 900}" name="source_citation {slide_index}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{footer_box.x}" y="{footer_box.y}"/><a:ext cx="{footer_box.cx}" cy="{footer_box.cy}"/></a:xfrm><a:noFill/><a:ln><a:noFill/></a:ln><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="r"/><a:r><a:rPr lang="en-US" sz="850"><a:solidFill><a:srgbClr val="{template.body_color}"/></a:solidFill><a:latin typeface="{template.font_family}"/></a:rPr><a:t>{_xml_text(text)}</a:t></a:r></a:p></p:txBody>
      </p:sp>'''


def _normalize_source_refs(source_refs: tuple[dict[str, Any], ...]) -> tuple[SourceReference, ...]:
    normalized: list[SourceReference] = []
    for index, item in enumerate(source_refs):
        kind = str(item.get("kind") or "source").strip() or "source"
        source_id = str(item.get("source_id") or f"source_{index + 1}").strip() or f"source_{index + 1}"
        role = str(item.get("role") or "primary_source").strip() or "primary_source"
        normalized.append(
            SourceReference(
                kind=kind,
                source_id=source_id,
                role=role,
                source_file_id=_optional_str(item.get("source_file_id")),
                source_document_id=_optional_str(item.get("source_document_id")),
                source_presentation_id=_optional_str(item.get("source_presentation_id")),
                derived_content_id=_optional_str(item.get("derived_content_id")),
            )
        )
    return tuple(normalized)


def _build_source_fragments(*, source_text: str, references: tuple[SourceReference, ...]) -> tuple[SourceFragment, ...]:
    text_fragments = _split_source_text(source_text)
    if not text_fragments:
        return ()
    fragments: list[SourceFragment] = []
    for index, excerpt in enumerate(text_fragments, start=1):
        source = references[(index - 1) % len(references)]
        fragments.append(
            SourceFragment(
                fragment_id=f"frag_{index:03d}",
                source=source,
                ordinal=index,
                excerpt=excerpt,
            )
        )
    return tuple(fragments)


def _split_source_text(source_text: str) -> tuple[str, ...]:
    normalized = source_text.replace("\r", "\n")
    candidates = [part.strip() for part in normalized.replace("\n", ". ").split(".") if part.strip()]
    if not candidates and source_text.strip():
        candidates = [source_text.strip()]
    return tuple(_clip(candidate, 160) for candidate in candidates[:20])


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clip(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"


def _xml_text(value: object) -> str:
    return escape(str(value), quote=False)
