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


def test_kr7e2_search_results_include_section_scores_and_coverage() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Finance\n\nRevenue retention improved after automation.\n\n# Operations\n\nDeployment risk decreased.",
        source_id="src_sections",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])

    results = index.search("revenue retention automation", limit=3)
    sections = index.search_sections("revenue retention automation", limit=3)

    assert results
    assert results[0].coverage_ratio >= 0.5
    assert results[0].section_id
    assert results[0].section_label
    assert results[0].section_score >= results[0].score
    assert sections
    assert sections[0].section_id == results[0].section_id
    assert "revenue" in sections[0].matched_terms
    assert results[0].evidence_id in sections[0].evidence_ids


def test_kr7e2_unsupported_claim_report_lists_missing_terms_and_candidate_sections() -> None:
    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"Customer churn decreased after support automation.",
        source_id="src_support",
        file_type="txt",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])

    assessment = index.assess_claim("customer churn decreased in Europe", min_coverage_ratio=0.9)

    assert assessment.status == "unsupported"
    assert assessment.unsupported_report is not None
    assert assessment.unsupported_report.schema_version == "offline_unsupported_claim_report.v1"
    assert "europe" in assessment.unsupported_report.missing_terms
    assert "customer" in assessment.unsupported_report.matched_terms
    assert assessment.unsupported_report.top_candidate_sections
    assert assessment.unsupported_report.required_action == "attach_source_or_revise_claim"


def test_kr7e2_prompt_only_unsupported_report_is_structured() -> None:
    index = OfflineEvidenceIndexBuilder().build_index([])

    assessment = index.assess_claim("market share increased")

    assert assessment.status == "unsupported"
    assert assessment.unsupported_report is not None
    assert assessment.unsupported_report.claim_terms == ("market", "share", "increased")
    assert assessment.unsupported_report.matched_terms == ()
    assert assessment.unsupported_report.missing_terms == ("market", "share", "increased")
    assert assessment.unsupported_report.top_candidate_sections == ()


def test_kr7e3_persists_and_loads_offline_evidence_index_without_absolute_paths(tmp_path) -> None:
    from backend.app.services.slides_service.offline_evidence_index import (
        OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION,
        OfflineEvidenceIndexStore,
    )

    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"# Evidence\n\nCustomer retention improved after support automation.",
        source_id="src_persist",
        file_type="md",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])

    store = OfflineEvidenceIndexStore(tmp_path / "evidence_indexes")
    result = store.persist_index(presentation_id="pres persist", index=index)
    loaded = store.load_index("pres persist")
    manifest = store.load_manifest("pres persist")

    assert result.schema_version == OFFLINE_EVIDENCE_INDEX_STORAGE_SCHEMA_VERSION
    assert result.status == "ready"
    assert result.index_relative_path == "pres_persist/offline_evidence_index.json"
    assert result.manifest_relative_path == "pres_persist/offline_evidence_index_manifest.json"
    assert loaded is not None
    assert loaded.schema_version == index.schema_version
    assert loaded.search("customer retention")
    assert manifest is not None
    assert manifest["checksum_verified"] is True
    assert str(tmp_path) not in str(manifest)


def test_kr7e3_loaded_evidence_index_preserves_unsupported_claim_reports(tmp_path) -> None:
    from backend.app.services.slides_service.offline_evidence_index import OfflineEvidenceIndexStore

    report = OfflineSourceIngestionEngine().ingest_bytes(
        b"Pipeline deployment risk decreased after automation.",
        source_id="src_loaded",
        file_type="txt",
    )
    index = OfflineEvidenceIndexBuilder().build_index([report])
    store = OfflineEvidenceIndexStore(tmp_path / "evidence_indexes")
    store.persist_index(presentation_id="pres_loaded", index=index)

    loaded = store.load_index("pres_loaded")
    assert loaded is not None
    assessment = loaded.assess_claim("deployment risk decreased in Europe", min_coverage_ratio=0.9)

    assert assessment.status == "unsupported"
    assert assessment.unsupported_report is not None
    assert "europe" in assessment.unsupported_report.missing_terms
    assert assessment.unsupported_report.required_action == "attach_source_or_revise_claim"
