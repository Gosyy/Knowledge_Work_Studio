#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_repo(repo_root: Path) -> dict[str, Any]:
    import sys

    sys.path.insert(0, str(repo_root))
    from backend.app.services.slides_service import (  # noqa: WPS433
        DATA_BACKED_CHARTS_SCHEMA_VERSION,
        DataChartRequest,
        bind_data_backed_charts,
        sample_data_backed_chart_report,
    )
    from backend.app.services.slides_service.offline_source_ingestion import (  # noqa: WPS433
        SourceChartDataCandidate,
        SourceTableCandidate,
    )

    table = SourceTableCandidate(
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
    bound = bind_data_backed_charts(
        [
            DataChartRequest(
                slide_id="s003",
                block_id="s003_revenue_chart",
                role="data",
                title="Quarterly revenue chart",
                intent_query="quarterly revenue cost chart",
                chart_type="line",
                expected_terms=("quarter", "revenue", "cost"),
                requires_chart=True,
            ),
            DataChartRequest(
                slide_id="s004",
                block_id="s004_retention_chart",
                role="data",
                title="Retention chart",
                intent_query="retention percent chart",
                chart_type="bar",
                expected_terms=("retention", "percent"),
                requires_chart=True,
            ),
        ],
        source_tables=[table],
        source_chart_candidates=[chart_candidate],
    ).as_dict()
    blocked = bind_data_backed_charts(
        [
            DataChartRequest(
                slide_id="s005",
                block_id="s005_missing_chart",
                role="data",
                title="Missing chart",
                intent_query="missing chart values",
                chart_type="line",
                expected_terms=("missing", "values"),
                requires_chart=True,
            )
        ],
        source_tables=[],
    ).as_dict()
    return {
        "schema_version": "kw_data_backed_charts_check.v1",
        "status": "ready",
        "chart_schema_version": DATA_BACKED_CHARTS_SCHEMA_VERSION,
        "sample": sample_data_backed_chart_report(),
        "bound": bound,
        "blocked": blocked,
        "problems": [],
    }


def _validate(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    chart_schema_version = report["chart_schema_version"]
    for name in ("sample", "bound"):
        payload = report.get(name) or {}
        if payload.get("schema_version") != chart_schema_version:
            problems.append(f"{name} schema version mismatch")
        if payload.get("status") != "ready":
            problems.append(f"{name} expected ready status")
        if payload.get("data_backed_charts_implemented") is not True:
            problems.append(f"{name} data-backed charts are not implemented")
        if payload.get("chart_intent_classification_implemented") is not True:
            problems.append(f"{name} chart intent classification missing")
        if payload.get("numeric_series_validation_implemented") is not True:
            problems.append(f"{name} numeric series validation missing")
        if payload.get("chart_data_binding_implemented") is not True:
            problems.append(f"{name} chart data binding missing")
        if payload.get("source_refs_required") is not True:
            problems.append(f"{name} source refs must be required")
        if payload.get("no_fake_charts_enforced") is not True:
            problems.append(f"{name} no fake charts guardrail missing")
        if payload.get("bound_chart_count", 0) < 1:
            problems.append(f"{name} expected at least one bound data-backed chart")
        if payload.get("generated_chart_data_allowed") is not False:
            problems.append(f"{name} generated chart data must not be allowed")
        if payload.get("random_chart_data_allowed") is not False:
            problems.append(f"{name} random chart data must not be allowed")
        if payload.get("fake_chart_data_allowed") is not False:
            problems.append(f"{name} fake chart data must not be allowed")
        if payload.get("bullet_length_charts_allowed") is not False:
            problems.append(f"{name} bullet-length charts must not be allowed")
        if payload.get("chart_without_data_source_allowed") is not False:
            problems.append(f"{name} chart without data source must not be allowed")
        if payload.get("renderer_runtime_changed") is not False:
            problems.append(f"{name} renderer runtime must remain unchanged")
        if payload.get("native_chart_rendering_implemented") is not False:
            problems.append(f"{name} native chart rendering must stay out of KR-7K contract patch")
        if payload.get("renderer_chart_mapping_implemented") is not False:
            problems.append(f"{name} renderer chart mapping must stay out of KR-7K contract patch")
        if payload.get("visual_qa_executed") is not False:
            problems.append(f"{name} visual QA must stay out of KR-7K")
        if payload.get("kimi_level_quality_claimed") is not False:
            problems.append(f"{name} Kimi-level quality must not be claimed")
        for binding in payload.get("chart_bindings", []):
            if binding.get("status") != "bound":
                problems.append(f"{name} binding {binding.get('block_id')} expected bound status")
                continue
            if not binding.get("data_ref") or not binding.get("provenance_ref"):
                problems.append(f"{name} binding {binding.get('block_id')} lacks data_ref/provenance_ref")
            if not binding.get("labels") or not binding.get("series"):
                problems.append(f"{name} binding {binding.get('block_id')} lacks labels/series")
    blocked = report.get("blocked") or {}
    if blocked.get("status") != "blocked":
        problems.append("blocked scenario must fail closed")
    if blocked.get("bound_chart_count") != 0:
        problems.append("blocked scenario must not bind a chart")
    if not blocked.get("errors"):
        problems.append("blocked scenario must explain missing numeric source data")
    if blocked.get("chart_without_data_source_allowed") is not False:
        problems.append("blocked scenario must keep chart_without_data_source_allowed=false")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KR-7K data-backed charts contract.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = _load_repo(repo_root)
    problems = _validate(report)
    if problems:
        report["status"] = "blocked"
        report["problems"] = problems
    print(f"kw_data_backed_charts_check.py: {report['status']}")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
