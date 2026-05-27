from __future__ import annotations

from backend.app.services.slides_service import (
    VISUAL_GRAMMAR_SCHEMA_VERSION,
    PresentationVisualGrammarLibrary,
    visual_grammar_catalog_payload,
)


def test_kr7g1_visual_grammar_catalog_contains_required_editable_blocks() -> None:
    catalog = visual_grammar_catalog_payload()
    block_types = {block["block_type"] for block in catalog["blocks"]}

    assert catalog["schema_version"] == VISUAL_GRAMMAR_SCHEMA_VERSION
    assert {
        "executive_summary_cards",
        "kpi_cards",
        "process_flow",
        "roadmap",
        "timeline",
        "two_by_two_matrix",
        "swot",
        "comparison_table",
        "decision_matrix",
        "risk_matrix",
        "architecture_diagram",
        "funnel",
        "data_table",
        "native_chart",
    } <= block_types
    assert "no_fake_charts_or_values" in catalog["non_goals"]
    assert all(block["semantic_purpose"] for block in catalog["blocks"])


def test_kr7g1_visual_grammar_validates_source_backed_cards() -> None:
    result = PresentationVisualGrammarLibrary().validate_block(
        {
            "block_id": "s002_summary",
            "type": "executive_summary_cards",
            "semantic_role": "executive_summary",
            "content": {"cards": [{"title": "Retention", "text": "Retention improved."}]},
            "source_refs": ["src_1#fragment_1"],
            "data_binding": None,
        }
    )

    assert result.schema_version == VISUAL_GRAMMAR_SCHEMA_VERSION
    assert result.status == "ready"
    assert result.issues == ()


def test_kr7g1_visual_grammar_blocks_chart_without_real_numeric_source_data() -> None:
    result = PresentationVisualGrammarLibrary().validate_block(
        {
            "block_id": "s003_chart",
            "type": "native_chart",
            "semantic_role": "evidence_chart",
            "content": {"chart_type": "bar", "series": [{"name": "A", "values": ["fake"]}]},
            "source_refs": ["src_table#rows"],
            "data_binding": {"source_ref": "src_table"},
        }
    )

    assert result.status == "blocked"
    issue_codes = {issue.code for issue in result.issues}
    assert "missing_data_binding_key" in issue_codes
    assert "native_chart_requires_real_numeric_data" in issue_codes


def test_kr7g1_visual_grammar_accepts_native_chart_with_source_data_ref_and_numeric_series() -> None:
    result = PresentationVisualGrammarLibrary().validate_block(
        {
            "block_id": "s003_chart",
            "type": "native_chart",
            "semantic_role": "evidence_chart",
            "content": {"chart_type": "bar", "series": [{"name": "Retention", "values": [71, 76, 82]}]},
            "source_refs": ["src_table#rows"],
            "data_binding": {"source_ref": "src_table", "data_ref": "src_table#rows:1-3"},
        }
    )

    assert result.status == "ready"


def test_kr7g1_visual_grammar_validates_diagram_nodes_or_items() -> None:
    blocked = PresentationVisualGrammarLibrary().validate_block(
        {
            "block_id": "s004_arch",
            "type": "architecture_diagram",
            "semantic_role": "architecture",
            "content": {"nodes": [], "edges": []},
            "source_refs": ["src_arch#section"],
            "data_binding": None,
        }
    )
    ready = PresentationVisualGrammarLibrary().validate_block(
        {
            "block_id": "s004_arch",
            "type": "architecture_diagram",
            "semantic_role": "architecture",
            "content": {"nodes": [{"id": "api"}], "edges": [{"from": "api", "to": "db"}]},
            "source_refs": ["src_arch#section"],
            "data_binding": None,
        }
    )

    assert blocked.status == "blocked"
    assert "missing_diagram_nodes_or_items" in {issue.code for issue in blocked.issues}
    assert ready.status == "ready"
