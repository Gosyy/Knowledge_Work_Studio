from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from typing import Any

from backend.app.services.slides_service.outline import PlannedSlide, PresentationPlan
from backend.app.services.slides_service.source_grounding import SlideCitation

K5_CHECKPOINT = "K5"
K5_SCHEMA_VERSION = "k5.source_to_slide_provenance_runtime.v1"
K5_WORKFLOW_ID = "k_phase.source_to_slide_provenance_runtime"
K_PHASE_BRANCH = "8_K_Phase"
K5_BASE_AFTER_K4 = "f85300b2497577d2034467cf356bebb77db98cc5"
K5_REDACTION_POLICY = "bounded_excerpt_preview_and_digest_only"
_FORBIDDEN_SAFE_TEXT = ("password", "secret", "token", "api_key", "client_secret", "authorization")

RCH2_CHECKPOINT = "RCH2"
RCH2_SCHEMA_VERSION = "rch2.provenance_fragment_quality.v1"
RCH2_WORKFLOW_ID = "release_candidate_hardening.provenance_fragment_quality"
RCH2_MIN_UNIQUE_FRAGMENT_RATIO = 0.75
RCH2_LOW_MATCH_SCORE_THRESHOLD = 1
P9_5_CHECKPOINT = "P9-5"
P9_5_SCHEMA_VERSION = "p9.5.operator_evidence_review.v1"
P9_5_BASE_AFTER_P9_4 = "647342bc420192bdf0267ef7ac31344eec786daa"
P9_5_MIN_USEFULNESS_SCORE = 3


@dataclass(frozen=True)
class K5SourceInput:
    source_id: str
    kind: str = "source"
    title: str = "Source"
    role: str = "primary_source"
    locator: str | None = None
    source_file_id: str | None = None
    source_document_id: str | None = None
    source_presentation_id: str | None = None
    derived_content_id: str | None = None
    checksum_sha256: str | None = None

    @property
    def source_label(self) -> str:
        return f"{self.kind}/{self.source_id}"

    def as_manifest_dict(self) -> dict[str, object]:
        payload = {
            "source_id": self.source_id,
            "kind": self.kind,
            "title": self.title,
            "role": self.role,
            "source_label": self.source_label,
        }
        for key in (
            "locator",
            "source_file_id",
            "source_document_id",
            "source_presentation_id",
            "derived_content_id",
            "checksum_sha256",
        ):
            value = getattr(self, key)
            if value:
                payload[key] = value
        return payload


@dataclass(frozen=True)
class K5SourceFragment:
    fragment_id: str
    source_id: str
    ordinal: int
    excerpt_preview: str
    excerpt_digest: str
    locator: str | None = None

    def as_manifest_dict(self) -> dict[str, object]:
        payload: dict[str, object] = asdict(self)
        if self.locator is None:
            payload.pop("locator")
        return payload


@dataclass(frozen=True)
class K5SlideEvidenceLink:
    slide_id: str
    slide_index: int
    citation_id: str
    source_id: str
    source_kind: str
    source_label: str
    fragment_id: str
    evidence_role: str
    excerpt_preview: str
    excerpt_digest: str
    claim_digest: str
    match_score: int = 0
    fragment_selection_reason: str = "deterministic_round_robin"
    diversity_rank: int = 0
    locator: str | None = None
    confidence: str = "deterministic_text_grounding"

    def as_manifest_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if self.locator is None:
            payload.pop("locator")
        return payload


@dataclass(frozen=True)
class K5OperatorEvidenceCard:
    slide_id: str
    slide_index: int
    citation_id: str
    source_label: str
    fragment_id: str
    claim_preview: str
    excerpt_preview: str
    match_score: int
    usefulness_score: int
    review_priority: str
    review_hint: str
    locator: str | None = None

    def as_manifest_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if self.locator is None:
            payload.pop("locator")
        return payload


@dataclass(frozen=True)
class K5CoverageReport:
    slide_count: int
    linked_slide_count: int
    source_count: int
    fragment_count: int
    uncovered_slide_ids: tuple[str, ...]
    coverage_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "slide_count": self.slide_count,
            "linked_slide_count": self.linked_slide_count,
            "source_count": self.source_count,
            "fragment_count": self.fragment_count,
            "uncovered_slide_ids": list(self.uncovered_slide_ids),
            "coverage_status": self.coverage_status,
            "coverage_ratio": 1.0 if self.slide_count == 0 else round(self.linked_slide_count / self.slide_count, 4),
        }


@dataclass(frozen=True)
class K5SourceToSlideProvenanceResult:
    plan: PresentationPlan
    sources: tuple[K5SourceInput, ...]
    fragments: tuple[K5SourceFragment, ...]
    slide_links: tuple[K5SlideEvidenceLink, ...]
    coverage: K5CoverageReport
    manifest_section: dict[str, object]
    safe_metadata: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "coverage": self.coverage.as_dict(),
            "source_count": len(self.sources),
            "fragment_count": len(self.fragments),
            "slide_link_count": len(self.slide_links),
            "safe_metadata": dict(self.safe_metadata),
        }


def build_k5_capabilities_report() -> dict[str, object]:
    return {
        "mode": "k5-source-to-slide-provenance-runtime",
        "checkpoint": K5_CHECKPOINT,
        "schema_version": K5_SCHEMA_VERSION,
        "workflow_id": K5_WORKFLOW_ID,
        "source_to_slide_provenance_supported": True,
        "slide_level_evidence_links_supported": True,
        "fragment_digest_supported": True,
        "bounded_excerpt_preview_supported": True,
        "plan_citation_enrichment_supported": True,
        "manifest_section_supported": True,
        "coverage_report_supported": True,
        "safe_redaction_supported": True,
        "fragment_quality_scoring_supported": True,
        "fragment_diversity_guard_supported": True,
        "slide_fragment_relevance_supported": True,
        "evidence_usefulness_metadata_supported": True,
        "offline_runtime_supported": True,
        "api_endpoint_added_by_k5": False,
        "db_schema_migration_added_by_k5": False,
        "frontend_runtime_changed_by_k5": False,
        "dependency_versions_changed_by_k5": False,
        "dockerfiles_changed_by_k5": False,
        "cloud_llm_added_by_k5": False,
        "cloud_vision_added_by_k5": False,
        "k6_end_to_end_workflow_added_by_k5": False,
        "kimi_level_claimed_by_k5": False,
        "whole_project_kimi_level_supported": False,
    }


def build_p9_5_capabilities_report() -> dict[str, object]:
    return {
        "p9_5_checkpoint": P9_5_CHECKPOINT,
        "p9_5_schema_version": P9_5_SCHEMA_VERSION,
        "p9_5_base_after_p9_4": P9_5_BASE_AFTER_P9_4,
        "p9_5_operator_evidence_review_supported": True,
        "operator_evidence_cards_supported": True,
        "evidence_review_manifest_section_supported": True,
        "human_provenance_usefulness_hardening_supported": True,
        "api_endpoint_added_by_p9_5": False,
        "db_schema_migration_added_by_p9_5": False,
        "frontend_runtime_changed_by_p9_5": False,
        "dependency_versions_changed_by_p9_5": False,
        "dockerfiles_changed_by_p9_5": False,
        "cloud_llm_added_by_p9_5": False,
        "cloud_vision_added_by_p9_5": False,
        "kimi_level_claimed_by_p9_5": False,
        "whole_project_kimi_level_supported_by_p9_5": False,
        "network_required_by_p9_5": False,
    }


def build_source_to_slide_provenance(
    plan: PresentationPlan,
    *,
    source_text: str,
    source_refs: tuple[dict[str, Any], ...] = (),
    max_excerpt_chars: int = 160,
) -> K5SourceToSlideProvenanceResult:
    """Build deterministic source-to-slide provenance for an approved plan.

    K5 is intentionally local and additive. It turns bounded source fragments
    into slide-level citations, a safe manifest section, and coverage metadata.
    It does not store raw source text in safe metadata and does not emit or
    persist artifacts by itself; RF2.6 remains the downloadable manifest layer.
    """

    _validate_plan(plan)
    sources = _normalize_sources(source_refs)
    if not sources:
        sources = (K5SourceInput(source_id="source_001", title="Operator supplied source"),)
    fragments = _build_fragments(source_text=source_text, sources=sources, max_excerpt_chars=max_excerpt_chars)
    if not fragments:
        raise ValueError("K5 source-to-slide provenance requires non-empty source_text fragments")

    updated_slides: list[PlannedSlide] = []
    slide_links: list[K5SlideEvidenceLink] = []
    source_by_id = {source.source_id: source for source in sources}
    fragment_use_counts: dict[str, int] = {}
    source_use_counts: dict[str, int] = {}

    for slide_index, slide in enumerate(plan.slides, start=1):
        fragment, match_score, selection_reason, diversity_rank = _select_fragment_for_slide(
            slide,
            fragments=fragments,
            fragment_use_counts=fragment_use_counts,
            source_use_counts=source_use_counts,
        )
        fragment_use_counts[fragment.fragment_id] = fragment_use_counts.get(fragment.fragment_id, 0) + 1
        source_use_counts[fragment.source_id] = source_use_counts.get(fragment.source_id, 0) + 1
        source = source_by_id[fragment.source_id]
        citation_id = f"k5_cite_{slide.slide_id}_{fragment.fragment_id}"
        citation = SlideCitation(
            citation_id=citation_id,
            source_kind=source.kind,
            source_id=source.source_id,
            fragment_id=fragment.fragment_id,
            source_label=source.source_label,
            excerpt=fragment.excerpt_preview,
            derived_content_id=source.derived_content_id,
        )
        claim_digest = _digest_payload(
            {
                "slide_id": slide.slide_id,
                "title": slide.title,
                "bullets": list(slide.bullets),
                "fragment_digest": fragment.excerpt_digest,
                "match_score": match_score,
                "selection_reason": selection_reason,
            }
        )
        link = K5SlideEvidenceLink(
            slide_id=slide.slide_id,
            slide_index=slide_index,
            citation_id=citation_id,
            source_id=source.source_id,
            source_kind=source.kind,
            source_label=source.source_label,
            fragment_id=fragment.fragment_id,
            evidence_role="primary_supporting_evidence",
            excerpt_preview=fragment.excerpt_preview,
            excerpt_digest=fragment.excerpt_digest,
            claim_digest=claim_digest,
            match_score=match_score,
            fragment_selection_reason=selection_reason,
            diversity_rank=diversity_rank,
            locator=fragment.locator or source.locator,
        )
        slide_links.append(link)
        source_note = (
            f"K5 provenance link {citation_id}: {source.source_label}#{fragment.fragment_id} "
            f"{fragment.excerpt_digest} match_score={match_score} reason={selection_reason}"
        )
        updated_slides.append(
            replace(
                slide,
                citations=tuple(slide.citations) + (citation,),
                source_notes=tuple(slide.source_notes) + (source_note,),
            )
        )

    enriched_plan = replace(plan, slides=tuple(updated_slides))
    coverage = _coverage_report(enriched_plan, tuple(slide_links), sources, fragments)
    evidence_cards = _operator_evidence_cards(enriched_plan, tuple(slide_links))
    manifest_section = _manifest_section(
        sources=sources,
        fragments=fragments,
        slide_links=tuple(slide_links),
        coverage=coverage,
        evidence_cards=evidence_cards,
    )
    metadata = _safe_metadata(
        plan=enriched_plan,
        sources=sources,
        fragments=fragments,
        slide_links=tuple(slide_links),
        coverage=coverage,
        manifest_section=manifest_section,
        evidence_cards=evidence_cards,
    )
    return K5SourceToSlideProvenanceResult(
        plan=enriched_plan,
        sources=sources,
        fragments=fragments,
        slide_links=tuple(slide_links),
        coverage=coverage,
        manifest_section=manifest_section,
        safe_metadata=metadata,
    )


def attach_k5_provenance_to_manifest(
    manifest: dict[str, Any],
    provenance_result: K5SourceToSlideProvenanceResult,
) -> dict[str, Any]:
    """Return a copy of an existing manifest with a K5 slide-level section.

    The existing RF2.6 manifest digest is preserved as-is. K5 adds its own
    section digest under integrity instead of pretending to re-sign the entire
    artifact manifest in this controlled patch.
    """

    updated = json.loads(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    updated["source_to_slide_provenance"] = provenance_result.manifest_section
    integrity = updated.setdefault("integrity", {})
    if isinstance(integrity, dict):
        integrity["k5_source_to_slide_section_digest"] = provenance_result.manifest_section["integrity"]["section_digest"]
        integrity["k5_redaction_policy"] = K5_REDACTION_POLICY
    return updated


def validate_k5_source_to_slide_result(result: K5SourceToSlideProvenanceResult) -> list[str]:
    errors: list[str] = []
    slide_ids = tuple(slide.slide_id for slide in result.plan.slides)
    linked_ids = tuple(link.slide_id for link in result.slide_links)
    if not result.sources:
        errors.append("K5 result has no sources")
    if not result.fragments:
        errors.append("K5 result has no source fragments")
    if set(slide_ids) != set(linked_ids):
        errors.append("K5 slide evidence links do not cover every slide exactly once")
    if len(linked_ids) != len(set(linked_ids)):
        errors.append("K5 slide evidence links contain duplicate slide ids")
    if result.coverage.coverage_status != "complete":
        errors.append(f"K5 coverage is not complete: {result.coverage.coverage_status}")
    if result.manifest_section.get("checkpoint") != K5_CHECKPOINT:
        errors.append("K5 manifest section checkpoint mismatch")
    if result.safe_metadata.get("raw_source_text_stored") is not False:
        errors.append("K5 safe metadata must not store raw source text")
    if result.safe_metadata.get("kimi_level_claimed_by_k5") is not False:
        errors.append("K5 must not claim Kimi-level")
    if not _verify_section_digest(result.manifest_section):
        errors.append("K5 manifest section digest does not verify")
    for slide in result.plan.slides:
        k5_citations = [citation for citation in slide.citations if getattr(citation, "citation_id", "").startswith("k5_cite_")]
        if not k5_citations:
            errors.append(f"slide {slide.slide_id} has no K5 citation")
    return errors



def _select_fragment_for_slide(
    slide: PlannedSlide,
    *,
    fragments: tuple[K5SourceFragment, ...],
    fragment_use_counts: dict[str, int],
    source_use_counts: dict[str, int],
) -> tuple[K5SourceFragment, int, str, int]:
    # RCH2: deterministic relevance and diversity scoring for bounded fragments.
    slide_terms = _evidence_terms(" ".join((slide.title, *slide.bullets)))
    best: tuple[int, int, int, int, K5SourceFragment, str] | None = None
    for fragment in fragments:
        fragment_terms = _evidence_terms(fragment.excerpt_preview)
        overlap = len(slide_terms.intersection(fragment_terms))
        title_overlap = len(_evidence_terms(slide.title).intersection(fragment_terms))
        bullet_overlap = len(_evidence_terms(" ".join(slide.bullets)).intersection(fragment_terms))
        reuse_penalty = fragment_use_counts.get(fragment.fragment_id, 0) * 3
        source_penalty = source_use_counts.get(fragment.source_id, 0)
        raw_score = (overlap * 3) + (title_overlap * 2) + bullet_overlap
        diversity_rank = fragment_use_counts.get(fragment.fragment_id, 0) + source_use_counts.get(fragment.source_id, 0)
        adjusted_score = raw_score - reuse_penalty - source_penalty
        reason = "term_overlap" if raw_score > 0 else "diversity_fallback"
        candidate = (adjusted_score, raw_score, -diversity_rank, -fragment.ordinal, fragment, reason)
        if best is None or candidate > best:
            best = candidate
    if best is None:
        raise ValueError("RCH2 fragment selection requires at least one source fragment")
    _adjusted, raw_score, neg_diversity_rank, _neg_ordinal, fragment, reason = best
    return fragment, int(raw_score), reason, int(-neg_diversity_rank)


def _fragment_quality_metrics(
    *,
    plan: PresentationPlan,
    sources: tuple[K5SourceInput, ...],
    fragments: tuple[K5SourceFragment, ...],
    slide_links: tuple[K5SlideEvidenceLink, ...],
) -> dict[str, object]:
    unique_fragment_ids = {link.fragment_id for link in slide_links}
    unique_source_ids = {link.source_id for link in slide_links}
    slide_count = max(1, len(plan.slides))
    unique_fragment_ratio = round(len(unique_fragment_ids) / slide_count, 4)
    source_diversity_ratio = round(len(unique_source_ids) / max(1, len(sources)), 4)
    average_match_score = round(sum(link.match_score for link in slide_links) / max(1, len(slide_links)), 4)
    low_quality_link_count = sum(1 for link in slide_links if link.match_score <= RCH2_LOW_MATCH_SCORE_THRESHOLD)
    repeated_fragment_count = max(0, len(slide_links) - len(unique_fragment_ids))
    selection_reasons = tuple(sorted({link.fragment_selection_reason for link in slide_links}))
    status = "good"
    if unique_fragment_ratio < RCH2_MIN_UNIQUE_FRAGMENT_RATIO or low_quality_link_count:
        status = "needs_human_review"
    if len(slide_links) != len(plan.slides) or not slide_links:
        status = "incomplete"
    return {
        "rch2_checkpoint": RCH2_CHECKPOINT,
        "rch2_schema_version": RCH2_SCHEMA_VERSION,
        "rch2_workflow_id": RCH2_WORKFLOW_ID,
        "rch2_provenance_fragment_quality_supported": True,
        "fragment_quality_scoring_supported": True,
        "fragment_diversity_guard_supported": True,
        "slide_fragment_relevance_supported": True,
        "evidence_usefulness_metadata_supported": True,
        "unique_fragment_ratio": unique_fragment_ratio,
        "source_diversity_ratio": source_diversity_ratio,
        "average_fragment_match_score": average_match_score,
        "low_quality_link_count": low_quality_link_count,
        "repeated_fragment_count": repeated_fragment_count,
        "fragment_selection_reasons": selection_reasons,
        "evidence_quality_status": status,
        "human_evidence_review_required": status != "good",
    }


def _evidence_terms(value: str) -> set[str]:
    terms: set[str] = set()
    for raw in value.lower().replace("_", " ").replace("-", " ").split():
        cleaned = "".join(char for char in raw if char.isalnum())
        if len(cleaned) < 4:
            continue
        if cleaned in {"slide", "source", "with", "from", "this", "that", "have", "will", "must", "into", "without"}:
            continue
        terms.add(cleaned)
    return terms

def _normalize_sources(source_refs: tuple[dict[str, Any], ...]) -> tuple[K5SourceInput, ...]:
    normalized: list[K5SourceInput] = []
    for index, item in enumerate(source_refs, start=1):
        source_id = _safe_short_text(item.get("source_id") or f"source_{index:03d}", 80)
        kind = _safe_short_text(item.get("kind") or "source", 40)
        title = _safe_short_text(item.get("title") or item.get("source_label") or source_id, 120)
        role = _safe_short_text(item.get("role") or "primary_source", 80)
        normalized.append(
            K5SourceInput(
                source_id=source_id or f"source_{index:03d}",
                kind=kind or "source",
                title=title or "Source",
                role=role or "primary_source",
                locator=_optional_short_text(item.get("locator"), 120),
                source_file_id=_optional_short_text(item.get("source_file_id"), 80),
                source_document_id=_optional_short_text(item.get("source_document_id"), 80),
                source_presentation_id=_optional_short_text(item.get("source_presentation_id"), 80),
                derived_content_id=_optional_short_text(item.get("derived_content_id"), 80),
                checksum_sha256=_normalize_checksum(item.get("checksum_sha256")),
            )
        )
    return tuple(normalized)


def _build_fragments(
    *,
    source_text: str,
    sources: tuple[K5SourceInput, ...],
    max_excerpt_chars: int,
) -> tuple[K5SourceFragment, ...]:
    fragments: list[K5SourceFragment] = []
    for ordinal, excerpt in enumerate(_split_source_text(source_text, max_excerpt_chars=max_excerpt_chars), start=1):
        source = sources[(ordinal - 1) % len(sources)]
        fragments.append(
            K5SourceFragment(
                fragment_id=f"k5_frag_{ordinal:03d}",
                source_id=source.source_id,
                ordinal=ordinal,
                excerpt_preview=excerpt,
                excerpt_digest=_digest_text(excerpt),
                locator=source.locator,
            )
        )
    return tuple(fragments)


def _split_source_text(source_text: str, *, max_excerpt_chars: int) -> tuple[str, ...]:
    normalized = " ".join(source_text.replace("\r", "\n").replace("\n", ". ").split())
    candidates = [part.strip() for part in normalized.split(".") if part.strip()]
    if not candidates and normalized:
        candidates = [normalized]
    return tuple(_safe_short_text(candidate, max_excerpt_chars) for candidate in candidates[:80] if candidate.strip())


def _coverage_report(
    plan: PresentationPlan,
    slide_links: tuple[K5SlideEvidenceLink, ...],
    sources: tuple[K5SourceInput, ...],
    fragments: tuple[K5SourceFragment, ...],
) -> K5CoverageReport:
    linked_ids = {link.slide_id for link in slide_links}
    uncovered = tuple(slide.slide_id for slide in plan.slides if slide.slide_id not in linked_ids)
    status = "complete" if not uncovered and len(linked_ids) == len(plan.slides) else "partial"
    return K5CoverageReport(
        slide_count=len(plan.slides),
        linked_slide_count=len(linked_ids),
        source_count=len(sources),
        fragment_count=len(fragments),
        uncovered_slide_ids=uncovered,
        coverage_status=status,
    )


def _manifest_section(
    *,
    sources: tuple[K5SourceInput, ...],
    fragments: tuple[K5SourceFragment, ...],
    slide_links: tuple[K5SlideEvidenceLink, ...],
    coverage: K5CoverageReport,
    evidence_cards: tuple[K5OperatorEvidenceCard, ...],
) -> dict[str, object]:
    section: dict[str, object] = {
        "schema_version": K5_SCHEMA_VERSION,
        "checkpoint": K5_CHECKPOINT,
        "workflow_id": K5_WORKFLOW_ID,
        "sources": [source.as_manifest_dict() for source in sources],
        "source_fragments": [fragment.as_manifest_dict() for fragment in fragments],
        "slide_evidence_links": [link.as_manifest_dict() for link in slide_links],
        "coverage": coverage.as_dict(),
        "operator_evidence_review": _operator_evidence_review_section(evidence_cards),
        "redaction": {
            "policy": K5_REDACTION_POLICY,
            "raw_source_text_stored": False,
            "raw_prompt_stored": False,
            "bounded_excerpt_preview_supported": True,
            "excerpt_digest_supported": True,
        },
        "integrity": {"section_digest": ""},
    }
    finalized = json.loads(json.dumps(section, ensure_ascii=False, sort_keys=True))
    finalized["integrity"]["section_digest"] = _digest_payload(finalized)
    return finalized



def _operator_evidence_cards(
    plan: PresentationPlan,
    slide_links: tuple[K5SlideEvidenceLink, ...],
) -> tuple[K5OperatorEvidenceCard, ...]:
    slide_by_id = {slide.slide_id: slide for slide in plan.slides}
    cards: list[K5OperatorEvidenceCard] = []
    for link in slide_links:
        slide = slide_by_id.get(link.slide_id)
        if slide is None:
            continue
        claim_preview = _claim_preview(slide)
        usefulness_score = _evidence_usefulness_score(slide=slide, link=link)
        review_priority = "operator_review" if usefulness_score < P9_5_MIN_USEFULNESS_SCORE else "spot_check"
        review_hint = (
            "Verify this slide claim against the cited fragment before release."
            if review_priority == "operator_review"
            else "Evidence card is suitable for operator spot check."
        )
        cards.append(
            K5OperatorEvidenceCard(
                slide_id=link.slide_id,
                slide_index=link.slide_index,
                citation_id=link.citation_id,
                source_label=link.source_label,
                fragment_id=link.fragment_id,
                claim_preview=claim_preview,
                excerpt_preview=link.excerpt_preview,
                match_score=link.match_score,
                usefulness_score=usefulness_score,
                review_priority=review_priority,
                review_hint=review_hint,
                locator=link.locator,
            )
        )
    return tuple(cards)


def _operator_evidence_review_section(evidence_cards: tuple[K5OperatorEvidenceCard, ...]) -> dict[str, object]:
    return {
        "schema_version": P9_5_SCHEMA_VERSION,
        "checkpoint": P9_5_CHECKPOINT,
        "evidence_cards": [card.as_manifest_dict() for card in evidence_cards],
        "summary": _operator_evidence_review_summary(evidence_cards),
        "redaction": {
            "raw_source_text_stored": False,
            "raw_prompt_stored": False,
            "bounded_claim_preview_supported": True,
            "bounded_excerpt_preview_supported": True,
        },
    }


def _operator_evidence_review_summary(evidence_cards: tuple[K5OperatorEvidenceCard, ...]) -> dict[str, object]:
    scores = tuple(card.usefulness_score for card in evidence_cards)
    low_count = sum(1 for score in scores if score < P9_5_MIN_USEFULNESS_SCORE)
    priorities = tuple(sorted({card.review_priority for card in evidence_cards}))
    return {
        "card_count": len(evidence_cards),
        "low_usefulness_card_count": low_count,
        "operator_evidence_review_required": low_count > 0,
        "min_usefulness_score": min(scores) if scores else 0,
        "average_usefulness_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "review_priorities": priorities,
    }


def _evidence_usefulness_score(*, slide: PlannedSlide, link: K5SlideEvidenceLink) -> int:
    score = 1
    if link.match_score >= 2:
        score += 1
    if link.fragment_selection_reason == "term_overlap":
        score += 1
    if len(_evidence_terms(link.excerpt_preview)) >= 4:
        score += 1
    if _evidence_terms(_claim_preview(slide)).intersection(_evidence_terms(link.excerpt_preview)):
        score += 1
    return min(score, 5)


def _claim_preview(slide: PlannedSlide) -> str:
    parts = [slide.title]
    parts.extend(slide.bullets[:2])
    return _safe_short_text(" — ".join(part for part in parts if part), 180)

def _safe_metadata(
    *,
    plan: PresentationPlan,
    sources: tuple[K5SourceInput, ...],
    fragments: tuple[K5SourceFragment, ...],
    slide_links: tuple[K5SlideEvidenceLink, ...],
    coverage: K5CoverageReport,
    manifest_section: dict[str, object],
    evidence_cards: tuple[K5OperatorEvidenceCard, ...],
) -> dict[str, object]:
    quality_metrics = _fragment_quality_metrics(
        plan=plan,
        sources=sources,
        fragments=fragments,
        slide_links=slide_links,
    )
    evidence_summary = _operator_evidence_review_summary(evidence_cards)
    metadata = {
        **build_k5_capabilities_report(),
        **build_p9_5_capabilities_report(),
        "slide_count": len(plan.slides),
        "source_count": len(sources),
        "fragment_count": len(fragments),
        "slide_evidence_link_count": len(slide_links),
        "coverage_status": coverage.coverage_status,
        "covered_slide_count": coverage.linked_slide_count,
        "uncovered_slide_count": len(coverage.uncovered_slide_ids),
        "source_ids": tuple(source.source_id for source in sources),
        "slide_ids": tuple(link.slide_id for link in slide_links),
        "fragment_digests": tuple(fragment.excerpt_digest for fragment in fragments),
        "section_digest": manifest_section["integrity"]["section_digest"],
        "operator_evidence_card_count": evidence_summary["card_count"],
        "low_usefulness_evidence_card_count": evidence_summary["low_usefulness_card_count"],
        "operator_evidence_review_required": evidence_summary["operator_evidence_review_required"],
        "evidence_usefulness_score_min": evidence_summary["min_usefulness_score"],
        "evidence_usefulness_score_average": evidence_summary["average_usefulness_score"],
        "evidence_card_review_priorities": evidence_summary["review_priorities"],
        **quality_metrics,
        "raw_source_text_stored": False,
        "raw_prompt_stored": False,
        "raw_sensitive_values_stored": False,
        "network_required": False,
    }
    _assert_safe_payload(metadata)
    return metadata


def _verify_section_digest(section: dict[str, object]) -> bool:
    integrity = section.get("integrity")
    if not isinstance(integrity, dict):
        return False
    expected = integrity.get("section_digest")
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        return False
    unsigned = json.loads(json.dumps(section, ensure_ascii=False, sort_keys=True))
    unsigned["integrity"]["section_digest"] = ""
    return expected == _digest_payload(unsigned)


def _validate_plan(plan: PresentationPlan) -> None:
    if not plan.slides:
        raise ValueError("K5 source-to-slide provenance requires at least one slide")
    if plan.target_slide_count != len(plan.slides):
        raise ValueError("K5 source-to-slide provenance requires target_slide_count to match slide count")
    for slide in plan.slides:
        if not slide.slide_id.strip():
            raise ValueError("K5 source-to-slide provenance requires slide_id on every slide")
        if not slide.title.strip():
            raise ValueError(f"K5 slide {slide.slide_id} has empty title")


def _normalize_checksum(value: object) -> str | None:
    text = _optional_short_text(value, 120)
    if not text:
        return None
    return text if text.startswith("sha256:") else f"sha256:{text}"


def _optional_short_text(value: object, limit: int) -> str | None:
    if value is None:
        return None
    text = _safe_short_text(value, limit)
    return text or None


def _safe_short_text(value: object, limit: int) -> str:
    cleaned = " ".join(str(value).replace("\n", " ").split())
    clipped = cleaned[:limit].strip()
    for forbidden in _FORBIDDEN_SAFE_TEXT:
        if forbidden in clipped.lower():
            return "[redacted]"
    return clipped


def _assert_safe_payload(payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in _FORBIDDEN_SAFE_TEXT:
        if forbidden in encoded:
            raise ValueError("K5 safe metadata contains forbidden secret-like value")


def _digest_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _digest_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(canonical).hexdigest()
