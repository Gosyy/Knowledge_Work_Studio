from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from backend.app.services.slides_service.offline_source_ingestion import SourceIngestionReport

OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION = "offline_evidence_index.v1"
OFFLINE_UNSUPPORTED_CLAIM_REPORT_SCHEMA_VERSION = "offline_unsupported_claim_report.v1"
OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION = "offline_evidence_index_storage.v1"

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
    section_id: str | None = None
    section_label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["keywords"] = list(self.keywords)
        return payload


@dataclass(frozen=True)
class EvidenceSectionScore:
    section_id: str
    source_id: str
    section_label: str
    score: float
    matched_terms: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_terms"] = list(self.matched_terms)
        payload["evidence_ids"] = list(self.evidence_ids)
        payload["provenance_refs"] = list(self.provenance_refs)
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
    coverage_ratio: float = 0.0
    section_id: str | None = None
    section_label: str | None = None
    section_score: float = 0.0
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_terms"] = list(self.matched_terms)
        return payload


@dataclass(frozen=True)
class UnsupportedClaimReport:
    schema_version: str
    claim: str
    reason: str
    claim_terms: tuple[str, ...]
    matched_terms: tuple[str, ...]
    missing_terms: tuple[str, ...]
    top_candidate_sections: tuple[EvidenceSectionScore, ...] = ()
    unsupported_sources: tuple[dict[str, Any], ...] = ()
    required_action: str = "attach_source_or_revise_claim"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["claim_terms"] = list(self.claim_terms)
        payload["matched_terms"] = list(self.matched_terms)
        payload["missing_terms"] = list(self.missing_terms)
        payload["top_candidate_sections"] = [section.as_dict() for section in self.top_candidate_sections]
        payload["unsupported_sources"] = list(self.unsupported_sources)
        return payload


@dataclass(frozen=True)
class ClaimEvidenceAssessment:
    claim: str
    status: str
    reason: str
    results: tuple[EvidenceSearchResult, ...] = ()
    unsupported_report: UnsupportedClaimReport | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["results"] = [result.as_dict() for result in self.results]
        payload["unsupported_report"] = self.unsupported_report.as_dict() if self.unsupported_report else None
        return payload


@dataclass(frozen=True)
class OfflineEvidenceIndexPersistenceResult:
    schema_version: str
    index_schema_version: str
    presentation_id: str
    status: str
    record_count: int
    source_count: int
    unsupported_source_count: int
    index_relative_path: str
    manifest_relative_path: str
    checksum_sha256: str
    size_bytes: int
    retrieval_contract: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class OfflineEvidenceIndexStore:
    """Persist and read offline evidence indexes without exposing operator paths.

    KR-7E.3 stores deterministic indexes produced by KR-7E.1/KR-7E.2.
    It is a read/persistence contract only: no web research, embeddings,
    PostgreSQL FTS runtime, PresentationIR planning, rendering, export, or UI
    source management is implemented here.
    """

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root)

    def persist_index(
        self,
        *,
        presentation_id: str,
        index: "OfflineEvidenceIndex",
    ) -> OfflineEvidenceIndexPersistenceResult:
        presentation_component = _safe_storage_component(presentation_id)
        index_relative_path = f"{presentation_component}/offline_evidence_index.json"
        manifest_relative_path = f"{presentation_component}/offline_evidence_index_manifest.json"
        index_path = self.storage_root / index_relative_path
        manifest_path = self.storage_root / manifest_relative_path
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_payload = index.as_dict()
        encoded = json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        index_path.write_bytes(encoded)
        checksum = hashlib.sha256(encoded).hexdigest()
        result = OfflineEvidenceIndexPersistenceResult(
            schema_version=OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION,
            index_schema_version=index.schema_version,
            presentation_id=presentation_id,
            status="ready",
            record_count=len(index.records),
            source_count=index.source_count,
            unsupported_source_count=len(index.unsupported_sources),
            index_relative_path=index_relative_path,
            manifest_relative_path=manifest_relative_path,
            checksum_sha256=checksum,
            size_bytes=len(encoded),
            retrieval_contract=dict(index.retrieval_contract),
        )
        manifest_path.write_text(
            json.dumps(result.as_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return result

    def load_index(self, presentation_id: str) -> "OfflineEvidenceIndex | None":
        presentation_component = _safe_storage_component(presentation_id)
        index_path = self.storage_root / presentation_component / "offline_evidence_index.json"
        if not index_path.is_file():
            return None
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        return offline_evidence_index_from_dict(payload)

    def load_manifest(self, presentation_id: str) -> dict[str, Any] | None:
        presentation_component = _safe_storage_component(presentation_id)
        manifest_path = self.storage_root / presentation_component / "offline_evidence_index_manifest.json"
        if not manifest_path.is_file():
            return None
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        encoded_index_path = self.storage_root / payload.get("index_relative_path", "")
        if encoded_index_path.is_file():
            checksum = hashlib.sha256(encoded_index_path.read_bytes()).hexdigest()
            payload["checksum_verified"] = checksum == payload.get("checksum_sha256")
        else:
            payload["checksum_verified"] = False
        return payload


@dataclass(frozen=True)
class OfflineEvidenceIndex:
    schema_version: str
    records: tuple[EvidenceFragmentRecord, ...]
    unsupported_sources: tuple[dict[str, Any], ...]
    source_count: int
    retrieval_contract: dict[str, Any]
    section_index: dict[str, tuple[str, ...]] = field(default_factory=dict)
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
            "section_index": {section_id: list(ids) for section_id, ids in sorted(self.section_index.items())},
            "inverted_index": {term: list(ids) for term, ids in sorted(self.inverted_index.items())},
            "document_frequency": dict(sorted(self.document_frequency.items())),
        }

    def search(self, query: str, *, limit: int = 5) -> tuple[EvidenceSearchResult, ...]:
        query_terms = tuple(_tokenize(query))
        if not query_terms:
            return ()
        scored_records, section_scores = self._score_query(query_terms)
        results: list[EvidenceSearchResult] = []
        for record, score, matched_terms, coverage_ratio in scored_records:
            section_score = section_scores.get(record.section_id or "", None)
            results.append(
                EvidenceSearchResult(
                    evidence_id=record.evidence_id,
                    source_id=record.source_id,
                    provenance_ref=record.provenance_ref,
                    text_preview=_preview(record.text),
                    score=score,
                    matched_terms=tuple(sorted(set(matched_terms))),
                    evidence_type=record.evidence_type,
                    coverage_ratio=coverage_ratio,
                    section_id=record.section_id,
                    section_label=record.section_label,
                    section_score=section_score.score if section_score else 0.0,
                    page_number=record.page_number,
                    slide_number=record.slide_number,
                    sheet_name=record.sheet_name,
                )
            )
        return tuple(sorted(results, key=lambda item: (-item.score, -item.section_score, item.evidence_id))[:limit])

    def search_sections(self, query: str, *, limit: int = 5) -> tuple[EvidenceSectionScore, ...]:
        query_terms = tuple(_tokenize(query))
        if not query_terms:
            return ()
        _, section_scores = self._score_query(query_terms)
        return tuple(sorted(section_scores.values(), key=lambda item: (-item.score, item.section_id))[:limit])

    def assess_claim(
        self,
        claim: str,
        *,
        min_score: float = 1.0,
        min_coverage_ratio: float = 0.5,
        limit: int = 5,
    ) -> ClaimEvidenceAssessment:
        claim_terms = tuple(_tokenize(claim))
        if not self.records:
            reason = "No local source evidence is indexed; prompt-only decks must not be treated as research-backed."
            return ClaimEvidenceAssessment(
                claim=claim,
                status="unsupported",
                reason=reason,
                unsupported_report=self._unsupported_claim_report(claim, claim_terms=claim_terms, reason=reason),
            )
        results = self.search(claim, limit=limit)
        matched_terms = tuple(sorted({term for result in results for term in result.matched_terms}))
        missing_terms = _missing_terms(claim_terms, matched_terms)
        best = results[0] if results else None
        if best is None or best.score < min_score or best.coverage_ratio < min_coverage_ratio:
            reason = "No indexed local evidence section met the lexical score and coverage thresholds."
            return ClaimEvidenceAssessment(
                claim=claim,
                status="unsupported",
                reason=reason,
                results=results,
                unsupported_report=self._unsupported_claim_report(
                    claim,
                    claim_terms=claim_terms,
                    matched_terms=matched_terms,
                    missing_terms=missing_terms,
                    reason=reason,
                ),
            )
        return ClaimEvidenceAssessment(
            claim=claim,
            status="supported",
            reason="At least one indexed local evidence section met the lexical score and coverage thresholds.",
            results=results,
        )

    def _score_query(
        self,
        query_terms: tuple[str, ...],
    ) -> tuple[list[tuple[EvidenceFragmentRecord, float, tuple[str, ...], float]], dict[str, EvidenceSectionScore]]:
        unique_query_terms = tuple(dict.fromkeys(query_terms))
        idf = _idf_by_term(self.document_frequency, document_count=max(1, len(self.records)))
        scored_records: list[tuple[EvidenceFragmentRecord, float, tuple[str, ...], float]] = []
        section_terms: dict[str, set[str]] = defaultdict(set)
        section_scores: Counter[str] = Counter()
        section_records: dict[str, list[EvidenceFragmentRecord]] = defaultdict(list)
        for record in self.records:
            term_counts = Counter(record.keywords)
            matched_terms = tuple(term for term in unique_query_terms if term in term_counts)
            if not matched_terms:
                continue
            coverage_ratio = len(set(matched_terms)) / max(1, len(set(unique_query_terms)))
            base = sum((1.0 + math.log(term_counts[term])) * idf.get(term, 1.0) for term in set(matched_terms))
            score = round(base * _section_boost(record) * (1.0 + coverage_ratio), 6)
            scored_records.append((record, score, matched_terms, round(coverage_ratio, 6)))
            section_id = record.section_id or _section_id(record)
            section_scores[section_id] += score
            section_terms[section_id].update(matched_terms)
            section_records[section_id].append(record)
        section_payload: dict[str, EvidenceSectionScore] = {}
        for section_id, score in section_scores.items():
            records = section_records[section_id]
            first = records[0]
            section_payload[section_id] = EvidenceSectionScore(
                section_id=section_id,
                source_id=first.source_id,
                section_label=first.section_label or section_id,
                score=round(float(score), 6),
                matched_terms=tuple(sorted(section_terms[section_id])),
                evidence_ids=tuple(record.evidence_id for record in records),
                provenance_refs=tuple(dict.fromkeys(record.provenance_ref for record in records)),
            )
        return scored_records, section_payload

    def _unsupported_claim_report(
        self,
        claim: str,
        *,
        claim_terms: tuple[str, ...],
        reason: str,
        matched_terms: tuple[str, ...] = (),
        missing_terms: tuple[str, ...] | None = None,
    ) -> UnsupportedClaimReport:
        missing = missing_terms if missing_terms is not None else _missing_terms(claim_terms, matched_terms)
        return UnsupportedClaimReport(
            schema_version=OFFLINE_UNSUPPORTED_CLAIM_REPORT_SCHEMA_VERSION,
            claim=claim,
            reason=reason,
            claim_terms=tuple(dict.fromkeys(claim_terms)),
            matched_terms=tuple(dict.fromkeys(matched_terms)),
            missing_terms=missing,
            top_candidate_sections=self.search_sections(claim, limit=3),
            unsupported_sources=self.unsupported_sources,
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

        section_index: dict[str, set[str]] = defaultdict(set)
        inverted: dict[str, set[str]] = defaultdict(set)
        document_frequency: Counter[str] = Counter()
        for record in records:
            if record.section_id:
                section_index[record.section_id].add(record.evidence_id)
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
                "methods": ["lexical_token_index", "bm25_like_idf_scoring", "source_section_boosting", "claim_term_coverage", "unsupported_claim_report"],
                "no_hidden_embedding_dependency": True,
                "no_web_research": True,
                "postgres_fts_runtime": "planned_not_claimed_in_kr7e1",
                "unsupported_claims_fail_closed": True,
                "section_scoring_hardened": True,
                "unsupported_claim_report_schema": OFFLINE_UNSUPPORTED_CLAIM_REPORT_SCHEMA_VERSION,
            },
            section_index={section_id: tuple(sorted(ids)) for section_id, ids in section_index.items()},
            inverted_index={term: tuple(sorted(ids)) for term, ids in inverted.items()},
            document_frequency=dict(document_frequency),
        )


def offline_evidence_index_from_dict(payload: dict[str, Any]) -> OfflineEvidenceIndex:
    if payload.get("schema_version") != OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION:
        raise ValueError(f"Unsupported offline evidence index schema_version: {payload.get('schema_version')}")
    records = tuple(_record_from_payload(item) for item in payload.get("records", []))
    return OfflineEvidenceIndex(
        schema_version=payload["schema_version"],
        records=records,
        unsupported_sources=tuple(dict(item) for item in payload.get("unsupported_sources", [])),
        source_count=int(payload.get("source_count", 0)),
        retrieval_contract=dict(payload.get("retrieval_contract", {})),
        section_index={str(key): tuple(value) for key, value in payload.get("section_index", {}).items()},
        inverted_index={str(key): tuple(value) for key, value in payload.get("inverted_index", {}).items()},
        document_frequency={str(key): int(value) for key, value in payload.get("document_frequency", {}).items()},
    )


def _record_from_payload(payload: dict[str, Any]) -> EvidenceFragmentRecord:
    return EvidenceFragmentRecord(
        evidence_id=str(payload["evidence_id"]),
        source_id=str(payload["source_id"]),
        source_kind=str(payload["source_kind"]),
        evidence_type=str(payload["evidence_type"]),
        text=str(payload.get("text") or ""),
        provenance_ref=str(payload["provenance_ref"]),
        keywords=tuple(payload.get("keywords", [])),
        fragment_id=payload.get("fragment_id"),
        table_id=payload.get("table_id"),
        structure_id=payload.get("structure_id"),
        chart_candidate_id=payload.get("chart_candidate_id"),
        role=payload.get("role"),
        page_number=payload.get("page_number"),
        slide_number=payload.get("slide_number"),
        sheet_name=payload.get("sheet_name"),
        section_id=payload.get("section_id"),
        section_label=payload.get("section_label"),
        metadata=dict(payload.get("metadata", {})),
    )


def _safe_storage_component(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    normalized = normalized.strip("._-")
    return normalized or "unknown"


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
        section_id=_section_id_from_fields(
            source_id=report.source_id,
            page_number=page_number,
            slide_number=slide_number,
            sheet_name=sheet_name,
            role=role,
            evidence_type=evidence_type,
        ),
        section_label=_section_label(
            source_id=report.source_id,
            page_number=page_number,
            slide_number=slide_number,
            sheet_name=sheet_name,
            role=role,
            evidence_type=evidence_type,
        ),
        metadata={"local_id": local_id, **(metadata or {})},
    )


def _missing_terms(claim_terms: tuple[str, ...], matched_terms: tuple[str, ...]) -> tuple[str, ...]:
    matched = set(matched_terms)
    return tuple(term for term in dict.fromkeys(claim_terms) if term not in matched)


def _section_id(record: EvidenceFragmentRecord) -> str:
    return record.section_id or _section_id_from_fields(
        source_id=record.source_id,
        page_number=record.page_number,
        slide_number=record.slide_number,
        sheet_name=record.sheet_name,
        role=record.role,
        evidence_type=record.evidence_type,
    )


def _section_id_from_fields(
    *,
    source_id: str,
    page_number: int | None,
    slide_number: int | None,
    sheet_name: str | None,
    role: str | None,
    evidence_type: str,
) -> str:
    if page_number is not None:
        return f"{source_id}#page:{page_number}"
    if slide_number is not None:
        return f"{source_id}#slide:{slide_number}"
    if sheet_name:
        return f"{source_id}#sheet:{_safe_section_component(sheet_name)}"
    if role in {"heading", "caption", "title"}:
        return f"{source_id}#section:{role}"
    return f"{source_id}#section:{evidence_type}"


def _section_label(
    *,
    source_id: str,
    page_number: int | None,
    slide_number: int | None,
    sheet_name: str | None,
    role: str | None,
    evidence_type: str,
) -> str:
    if page_number is not None:
        return f"{source_id} page {page_number}"
    if slide_number is not None:
        return f"{source_id} slide {slide_number}"
    if sheet_name:
        return f"{source_id} sheet {sheet_name}"
    if role in {"heading", "caption", "title"}:
        return f"{source_id} {role}"
    return f"{source_id} {evidence_type}"


def _safe_section_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-") or "section"


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
    "OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION",
    "ClaimEvidenceAssessment",
    "EvidenceSectionScore",
    "EvidenceFragmentRecord",
    "EvidenceSearchResult",
    "OfflineEvidenceIndex",
    "OfflineEvidenceIndexBuilder",
    "OfflineEvidenceIndexPersistenceResult",
    "OfflineEvidenceIndexStore",
    "UnsupportedClaimReport",
    "offline_evidence_index_from_dict",
]
