from __future__ import annotations

from backend.app.services.slides_service.offline_evidence_index import (
    OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION,
    OfflineEvidenceIndexBuilder,
)
from backend.app.services.slides_service.offline_source_ingestion import OfflineSourceIngestionEngine


def test_kr7e_evidence_index_builds_lexical_records_from_ingestion_report() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        """# Revenue growth

Revenue increased by 42 percent after the launch.

| Metric | Value |
| --- | --- |
| Revenue | 42% |
""".encode(),
        source_id="src_md",
        file_type="md",
    )

    index = OfflineEvidenceIndexBuilder().build_index([report])

    assert index.schema_version == OFFLINE_EVIDENCE_INDEX_SCHEMA_VERSION
    assert index.source_count == 1
    assert index.records
    assert index.retrieval_contract["no_hidden_embedding_dependency"] is True
    assert index.retrieval_contract["no_web_research"] is True
    assert index.retrieval_contract["postgres_fts_runtime"] == "planned_not_claimed_in_kr7e1"
    assert "revenue" in index.inverted_index


def test_kr7e_evidence_index_search_returns_source_backed_evidence() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Roadmap\n\nThe migration roadmap reduces operational risk and improves provenance.",
        source_id="src_roadmap",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])

    results = index.search("operational risk provenance", limit=3)

    assert results
    assert results[0].source_id == "src_roadmap"
    assert "provenance" in results[0].matched_terms
    assert results[0].provenance_ref.startswith("src_roadmap#")


def test_kr7e_evidence_index_assesses_supported_and_unsupported_claims() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"Source evidence says customer churn decreased after support automation.",
        source_id="src_claims",
        file_type="txt",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])

    supported = index.assess_claim("customer churn decreased after support automation")
    unsupported = index.assess_claim("gross margin doubled in Europe")

    assert supported.status == "supported"
    assert supported.results
    assert unsupported.status == "unsupported"
    assert "No indexed local evidence" in unsupported.reason


def test_kr7e_prompt_only_index_does_not_claim_research_backing() -> None:
    index = OfflineEvidenceIndexBuilder().build_index([])

    assessment = index.assess_claim("market share increased")

    assert assessment.status == "unsupported"
    assert assessment.results == ()
    assert "prompt-only decks must not be treated as research-backed" in assessment.reason


def test_kr7e_unsupported_sources_are_reported_honestly() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(b"\x00\x01", source_id="src_bin", file_type="bin")

    index = OfflineEvidenceIndexBuilder().build_index([report])

    assert index.records == ()
    assert index.unsupported_sources[0]["source_id"] == "src_bin"
    assert index.unsupported_sources[0]["status"] == "unsupported"
