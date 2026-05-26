from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from backend.app.services.slides_service.offline_source_ingestion import SourceIngestionReport

OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION = "offline_evidence_index.v1"

_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{2,}", flags=re.UNICODE)
_STOPWORDS = {
    "and",
    "for",
    "the",
    "with",
    "this",
    "that",
    "from",
    "into",
    "без",
    "для",
    "или",
    "как",
    "это",
    "что",
    "при",
    "над",
    "под",
    "the",
}


@dataclass(frozen=True)
class EvidenceFragmentRecord:
    evidence_id: str
    source_id: str
    source_kind: str
    evidence_type: str
    text: str
    provenance_ref: str
    keywords: tuple[str, ...]
    fragment_id: str | None = None
    table_id: str | None = None
    structure_id: str | None = None
    chart_candidate_id: str | None = None
    role: str | None = None
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["keywords"] = list(self.keywords)
        return payload


@dataclass(frozen=True)
class EvidenceSearchResult:
    evidence_id: str
    source_id: str
    provenance_ref: str
    text_preview: str
    score: float
    matched_terms: tuple[str, ...]
    evidence_type: str
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_terms"] = list(self.matched_terms)
        return payload


@dataclass(frozen=True)
class ClaimEvidenceAssessment:
    claim: str
    status: str
    reason: str
    results: tuple[EvidenceSearchResult, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["results"] = [result.as_dict() for result in self.results]
        return payload


@dataclass(frozen=True)
class OfflineEvidenceIndex:
    schema_version: str
    records: tuple[EvidenceFragmentRecord, ...]
    unsupported_sources: tuple[dict[str, Any], ...]
    source_count: int
    retrieval_contract: dict[str, Any]
    inverted_index: dict[str, tuple[str, ...]] = field(default_factory=dict)
    document_frequency: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_count": self.source_count,
            "record_count": len(self.records),
            "records": [record.as_dict() for record in self.records],
            "unsupported_sources": list(self.unsupported_sources),
            "retrieval_contract": self.retrieval_contract,
            "inverted_index": {term: list(ids) for term, ids in sorted(self.inverted_index.items())},
            "document_frequency": dict(sorted(self.document_frequency.items())),
        }

    def search(self, query: str, *, limit: int = 5) -> tuple[EvidenceSearchResult, ...]:
        query_terms = tuple(_tokenize(query))
        if not query_terms:
            return ()
        idf = _idf_by_term(self.document_frequency, document_count=max(1, len(self.records)))
        scored: list[EvidenceSearchResult] = []
        for record in self.records:
            term_counts = Counter(record.keywords)
            matched_terms = tuple(term for term in query_terms if term in term_counts)
            if not matched_terms:
                continue
            base = sum((1.0 + math.log(term_counts[term])) * idf.get(term, 1.0) for term in set(matched_terms))
            score = round(base * _section_boost(record), 6)
            scored.append(
                EvidenceSearchResult(
                    evidence_id=record.evidence_id,
                    source_id=record.source_id,
                    provenance_ref=record.provenance_ref,
                    text_preview=_preview(record.text),
                    score=score,
                    matched_terms=tuple(sorted(set(matched_terms))),
                    evidence_type=record.evidence_type,
                    page_number=record.page_number,
                    slide_number=record.slide_number,
                    sheet_name=record.sheet_name,
                )
            )
        return tuple(sorted(scored, key=lambda item: (-item.score, item.evidence_id))[:limit])

    def assess_claim(self, claim: str, *, min_score: float = 1.0, limit: int = 5) -> ClaimEvidenceAssessment:
        if not self.records:
            return ClaimEvidenceAssessment(
                claim=claim,
                status="unsupported",
                reason="No local source evidence is indexed; prompt-only decks must not be treated as research-backed.",
            )
        results = self.search(claim, limit=limit)
        if not results or results[0].score < min_score:
            return ClaimEvidenceAssessment(
                claim=claim,
                status="unsupported",
                reason="No indexed local evidence fragment met the lexical support threshold.",
                results=results,
            )
        return ClaimEvidenceAssessment(
            claim=claim,
            status="supported",
            reason="At least one indexed local evidence fragment matched the lexical support threshold.",
            results=results,
        )


class OfflineEvidenceIndexBuilder:
    """Build a deterministic offline lexical evidence index from ingestion reports.

    KR-7E.1 intentionally uses local fragments, tables, structures and chart
    candidates only. It does not call web search, LLMs, embeddings, OCR,
    PresentationIR planners, renderers, or UI source managers.
    """

    def build_index(self, reports: Iterable[SourceIngestionReport]) -> OfflineEvidenceIndex:
        reports = tuple(reports)
        records: list[EvidenceFragmentRecord] = []
        unsupported_sources: list[dict[str, Any]] = []
        for report in reports:
            if report.status != "ready":
                unsupported_sources.append(
                    {
                        "source_id": report.source_id,
                        "source_kind": report.source_kind,
                        "status": report.status,
                        "warnings": list(report.warnings),
                        "errors": list(report.errors),
                    }
                )
                continue
            records.extend(_records_from_report(report))

        inverted: dict[str, set[str]] = defaultdict(set)
        document_frequency: Counter[str] = Counter()
        for record in records:
            unique_terms = set(record.keywords)
            for term in unique_terms:
                inverted[term].add(record.evidence_id)
                document_frequency[term] += 1
        return OfflineEvidenceIndex(
            schema_version=OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION,
            records=tuple(records),
            unsupported_sources=tuple(unsupported_sources),
            source_count=len(reports),
            retrieval_contract={
                "methods": ["lexical_token_index", "bm25_like_idf_scoring", "source_section_boosting"],
                "no_hidden_embedding_dependency": True,
                "no_web_research": True,
                "postgres_fts_runtime": "planned_not_claimed_in_kr7e1",
                "unsupported_claims_fail_closed": True,
            },
            inverted_index={term: tuple(sorted(ids)) for term, ids in inverted.items()},
            document_frequency=dict(document_frequency),
        )


def _records_from_report(report: SourceIngestionReport) -> list[EvidenceFragmentRecord]:
    records: list[EvidenceFragmentRecord] = []
    for index, fragment in enumerate(report.fragments, start=1):
        records.append(
            _record(
                report=report,
                evidence_type="fragment",
                text=fragment.text,
                provenance_ref=fragment.provenance_ref,
                local_id=fragment.fragment_id,
                ordinal=index,
                fragment_id=fragment.fragment_id,
                role=fragment.role,
                page_number=fragment.page_number,
                slide_number=fragment.slide_number,
                sheet_name=fragment.sheet_name,
                metadata={"heading_level": fragment.heading_level},
            )
        )
    for index, table in enumerate(report.tables, start=1):
        text = _table_text(table.rows)
        records.append(
            _record(
                report=report,
                evidence_type="table",
                text=text,
                provenance_ref=table.provenance_ref,
                local_id=table.table_id,
                ordinal=index,
                table_id=table.table_id,
                role="table",
                page_number=table.page_number,
                slide_number=table.slide_number,
                sheet_name=table.sheet_name,
                metadata={"caption": table.caption, "has_formula": table.has_formula, "row_count": len(table.rows)},
            )
        )
    for index, structure in enumerate(report.structures, start=1):
        text = structure.text or structure.role or structure.element_type
        records.append(
            _record(
                report=report,
                evidence_type="structure",
                text=text,
                provenance_ref=structure.provenance_ref,
                local_id=structure.element_id,
                ordinal=index,
                structure_id=structure.element_id,
                role=structure.role,
                page_number=structure.page_number,
                slide_number=structure.slide_number,
                sheet_name=structure.sheet_name,
                metadata={"element_type": structure.element_type, **structure.metadata},
            )
        )
    for index, chart in enumerate(report.chart_candidates, start=1):
        text = " ".join([chart.title or chart.chart_type, *chart.data_refs]).strip()
        records.append(
            _record(
                report=report,
                evidence_type="chart_candidate",
                text=text,
                provenance_ref=chart.provenance_ref,
                local_id=chart.candidate_id,
                ordinal=index,
                chart_candidate_id=chart.candidate_id,
                role="chart_candidate",
                slide_number=chart.slide_number,
                sheet_name=chart.sheet_name,
                metadata={"chart_type": chart.chart_type, "data_refs": list(chart.data_refs), **chart.metadata},
            )
        )
    return [record for record in records if record.keywords]


def _record(
    *,
    report: SourceIngestionReport,
    evidence_type: str,
    text: str,
    provenance_ref: str,
    local_id: str,
    ordinal: int,
    fragment_id: str | None = None,
    table_id: str | None = None,
    structure_id: str | None = None,
    chart_candidate_id: str | None = None,
    role: str | None = None,
    page_number: int | None = None,
    slide_number: int | None = None,
    sheet_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> EvidenceFragmentRecord:
    return EvidenceFragmentRecord(
        evidence_id=f"{report.source_id}_evidence_{evidence_type}_{ordinal:03d}",
        source_id=report.source_id,
        source_kind=report.source_kind,
        evidence_type=evidence_type,
        text=text,
        provenance_ref=provenance_ref,
        keywords=tuple(_tokenize(text)),
        fragment_id=fragment_id,
        table_id=table_id,
        structure_id=structure_id,
        chart_candidate_id=chart_candidate_id,
        role=role,
        page_number=page_number,
        slide_number=slide_number,
        sheet_name=sheet_name,
        metadata={"local_id": local_id, **(metadata or {})},
    )


def _tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in _TOKEN_RE.findall(text or "")]
    return [token for token in tokens if token not in _STOPWORDS]


def _table_text(rows: list[list[str]]) -> str:
    return "\n".join(" | ".join(cell for cell in row if cell is not None) for row in rows)


def _preview(text: str, *, max_chars: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def _idf_by_term(document_frequency: dict[str, int], *, document_count: int) -> dict[str, float]:
    return {
        term: math.log(1 + (document_count + 1) / (frequency + 1)) + 1.0
        for term, frequency in document_frequency.items()
    }


def _section_boost(record: EvidenceFragmentRecord) -> float:
    if record.role in {"heading", "caption", "title"}:
        return 1.25
    if record.evidence_type in {"table", "chart_candidate"}:
        return 1.15
    return 1.0


__all__ = [
    "OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION",
    "ClaimEvidenceAssessment",
    "EvidenceFragmentRecord",
    "EvidenceSearchResult",
    "OfflineEvidenceIndex",
    "OfflineEvidenceIndexBuilder",
]
