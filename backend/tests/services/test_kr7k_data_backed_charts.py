from __future__ import annotations

from backend.app.services.slides_service import (
    DATA_BACKED_CHARTS_SCHEMA_VERSION,
    DataChartRequest,
    bind_data_backed_charts,
    sample_data_backed_chart_report,
)
from backend.app.services.slides_service.data_backed_charts import DataChartSourceCandidate
from backend.app.services.slides_service.offline_source_ingestion import SourceChartDataCandidate, SourceTableCandidate


def _revenue_table() -> SourceTableCandidate:
    return SourceTableCandidate(
        table_id="revenue_table",
        source_id="uploaded_finance_workbook",
        rows=[
            ["Quarter", "Revenue", "Cost"],
            ["Q1", "120", "75"],
            ["Q2", "135", "80"],
            ["Q3", "160", "92"],
            ["Q4", "172", "101"],
        ],
        provenance_ref="uploaded_finance_workbook#xlsx-sheet:1!A1:C5",
        caption="Quarterly revenue and cost, USD thousands",
        sheet_name="Finance",
    )


def _request() -> DataChartRequest:
    return DataChartRequest(
        slide_id="s003",
        block_id="s003_revenue_chart",
        role="data",
        title="Quarterly revenue chart",
        intent_query="quarterly revenue cost chart",
        chart_type="line",
        expected_terms=("quarter", "revenue", "cost"),
        requires_chart=True,
    )


def test_kr7k_sample_data_backed_chart_report_is_ready() -> None:
    report = sample_data_backed_chart_report()

    assert report["schema_version"] == DATA_BACKED_CHARTS_SCHEMA_VERSION
    assert report["phase"] == "KR-7K data-backed charts"
    assert report["status"] == "ready"
    assert report["data_backed_charts_implemented"] is True
    assert report["chart_intent_classification_implemented"] is True
    assert report["numeric_series_validation_implemented"] is True
    assert report["chart_data_binding_implemented"] is True
    assert report["source_refs_required"] is True
    assert report["no_fake_charts_enforced"] is True
    assert report["bound_chart_count"] == 1
    assert report["candidate_count"] == 1

    binding = report["chart_bindings"][0]
    assert binding["status"] == "bound"
    assert binding["data_ref"]
    assert binding["provenance_ref"] == "uploaded_finance_workbook#xlsx-sheet:1!A1:C5"
    assert binding["labels"] == ["Q1", "Q2", "Q3", "Q4"]
    assert binding["series"][0]["values"] == [120.0, 135.0, 160.0, 172.0]
    assert binding["units"] == "USD"

    assert report["generated_chart_data_allowed"] is False
    assert report["random_chart_data_allowed"] is False
    assert report["fake_chart_data_allowed"] is False
    assert report["bullet_length_charts_allowed"] is False
    assert report["chart_without_data_source_allowed"] is False
    assert report["renderer_runtime_changed"] is False
    assert report["native_chart_rendering_implemented"] is False
    assert report["renderer_chart_mapping_implemented"] is False
    assert report["visual_qa_executed"] is False
    assert report["kimi_level_quality_claimed"] is False
    assert "no_native_chart_rendering_runtime" in report["non_goals"]


def test_kr7k_binds_chart_request_to_real_numeric_source_table() -> None:
    result = bind_data_backed_charts([_request()], source_tables=[_revenue_table()])
    report = result.as_dict()

    assert report["status"] == "ready"
    assert report["chart_bindings"][0]["status"] == "bound"
    assert report["chart_bindings"][0]["data_id"] == "table_chart_data_revenue_table"
    assert report["chart_bindings"][0]["matched_terms"]
    assert report["chart_bindings"][0]["source_id"] == "uploaded_finance_workbook"
    assert report["chart_bindings"][0]["data_ref"].endswith("#revenue_table")


def test_kr7k_rejects_chart_without_numeric_source_data() -> None:
    empty_result = bind_data_backed_charts([_request()], source_tables=[]).as_dict()

    assert empty_result["status"] == "blocked"
    assert empty_result["bound_chart_count"] == 0
    assert empty_result["chart_bindings"][0]["status"] == "blocked"
    assert empty_result["chart_bindings"][0]["blocked_reason"] == "required_chart_has_no_real_numeric_source_data"
    assert empty_result["chart_without_data_source_allowed"] is False
    assert empty_result["errors"]


def test_kr7k_rejects_fake_or_generated_chart_data() -> None:
    candidate = DataChartSourceCandidate(
        data_id="fake_market_projection",
        source_kind="user_provided_numeric_data",
        source_id="prompt_only",
        provenance_ref="prompt_only#fake-chart",
        data_ref="prompt_only#fake-chart",
        labels=("A", "B", "C"),
        series=(),
        fake_data=True,
    )

    report = bind_data_backed_charts([_request()], user_data_candidates=[candidate]).as_dict()

    assert report["status"] == "blocked"
    assert report["fake_chart_data_allowed"] is False
    assert any("not source-backed real data" in error for error in report["errors"])


def test_kr7k_rejects_bullet_length_charts() -> None:
    bullet_table = SourceTableCandidate(
        table_id="bullet_table",
        source_id="uploaded_notes",
        rows=[
            ["Topic", "Impact"],
            ["- market grew because leadership invested in long narrative bullets", "5"],
            ["- cost reduced after consolidation", "3"],
        ],
        provenance_ref="uploaded_notes#markdown-table:1",
    )

    report = bind_data_backed_charts([_request()], source_tables=[bullet_table]).as_dict()

    assert report["status"] == "blocked"
    assert report["bullet_length_charts_allowed"] is False
    assert any("bullet text" in error for error in report["errors"])


def test_kr7k_can_bind_from_source_chart_candidate_when_numeric_series_is_extracted() -> None:
    chart_candidate = SourceChartDataCandidate(
        candidate_id="xlsx_chart_001",
        source_id="uploaded_workbook",
        chart_type="barChart",
        provenance_ref="uploaded_workbook#xlsx-chart:1:xl/charts/chart1.xml",
        data_refs=["uploaded_workbook#Finance!A1:B4"],
        title="Retention",
        sheet_name="Finance",
        metadata={
            "labels": ["Jan", "Feb", "Mar"],
            "series": [{"name": "Retention", "values": [71, 76, 82]}],
            "units": "percent",
        },
    )
    request = DataChartRequest(
        slide_id="s004",
        block_id="s004_retention_chart",
        role="data",
        title="Retention chart",
        intent_query="retention percent chart",
        chart_type="bar",
        expected_terms=("retention", "percent"),
        requires_chart=True,
    )

    report = bind_data_backed_charts([request], source_chart_candidates=[chart_candidate]).as_dict()

    assert report["status"] == "ready"
    binding = report["chart_bindings"][0]
    assert binding["status"] == "bound"
    assert binding["data_ref"] == "uploaded_workbook#Finance!A1:B4"
    assert binding["units"] == "percent"
    assert binding["series"][0]["values"] == [71.0, 76.0, 82.0]
