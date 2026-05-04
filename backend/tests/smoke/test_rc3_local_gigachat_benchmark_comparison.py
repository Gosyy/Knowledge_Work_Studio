from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rc3_local_gigachat_benchmark_comparison_runs_fallback_baseline(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "rc3-artifacts"
    report_out = tmp_path / "rc3-report.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_rc3_local_gigachat_benchmark_comparison.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(artifacts_dir),
            "--report-out",
            str(report_out),
            "--json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)

    assert report["checkpoint"] == "RC3"
    assert report["status"] == "ready"
    assert report["local_gigachat_golden_benchmark_comparison_supported"] is True
    assert report["fallback_baseline_supported"] is True
    assert report["fallback_cases_executed"] == 5
    assert report["fallback_cases_ready"] == 5
    assert report["plan_digest_comparisons_generated"] is True
    assert report["artifact_delta_comparisons_generated"] is True
    assert report["visual_qa_delta_comparisons_generated"] is True
    assert report["provenance_coverage_compared"] is True
    assert report["human_benchmark_review_required"] is True
    assert report["feature_runtime_added_by_rc3"] is False
    assert report["api_endpoint_added_by_rc3"] is False
    assert report["db_schema_migration_added_by_rc3"] is False
    assert report["frontend_runtime_changed_by_rc3"] is False
    assert report["dependency_versions_changed_by_rc3"] is False
    assert report["dockerfiles_changed_by_rc3"] is False
    assert report["cloud_llm_added_by_rc3"] is False
    assert report["cloud_vision_added_by_rc3"] is False
    assert report["public_internet_required"] is False
    assert report["kimi_level_claimed_by_rc3"] is False
    assert report["whole_project_kimi_level_supported"] is False
    assert report["errors"] == []
    assert report_out.exists()

    assert report["gigachat_provider_route"] in {"local_intranet", "public_api_dev"}
    if report["gigachat_endpoint_configured"]:
        assert report["comparison_status"] in {
            "compared_local_gigachat_to_fallback",
            "partial_local_gigachat_comparison",
            "gigachat_endpoint_attempted_but_k1_fallback_used",
        }
    else:
        assert report["comparison_status"] == "skipped_no_local_endpoint_configured"

    for case in report["case_comparisons"]:
        assert case["fallback_workflow_status"] == "ready_for_operator_delivery"
        assert case["fallback_slide_count"] == case["local_slide_count"]
        assert case["provenance_coverage_match"] is True
        assert case["errors"] == []




def test_rc3_public_gigachat_parser_normalizes_fenced_nested_json() -> None:
    from scripts.kw_rc3_local_gigachat_benchmark_comparison import _normalize_plan_text_for_k1

    prompt = json.dumps({"target_slide_count": 5}, ensure_ascii=False)
    raw = """
    Ниже план презентации:
    ```json
    {
      "presentation": {
        "presentation_title": "Architecture Review",
        "sections": [
          {"heading": "Context", "points": ["Current state", "Constraint"]},
          {"heading": "Target", "points": ["North star", "Quality gate"]},
          {"heading": "Risks", "points": ["Integration", "Operations"]},
          {"heading": "Decision", "points": ["Recommended option", "Next step"]}
        ]
      }
    }
    ```
    """
    normalized = json.loads(_normalize_plan_text_for_k1(raw, prompt))
    assert normalized["deck_title"] == "Architecture Review"
    assert len(normalized["slides"]) == 4
    assert normalized["slides"][0]["title"] == "Context"
    assert normalized["slides"][0]["bullets"] == ["Current state", "Constraint"]
    assert normalized["slides"][0]["slide_type"] in {"title", "content", "section"}
def test_rc3_public_gigachat_normalizer_synthesizes_parseable_plan_from_text() -> None:
    import json

    from scripts.kw_rc3_local_gigachat_benchmark_comparison import _normalize_plan_text_for_k1

    prompt = json.dumps({'target_slide_count': 5}, ensure_ascii=False)
    raw_answer = """Архитектурная цель: разделить ingestion, planning и renderer.
    Риск: таблицы и длинные документы требуют контроля плотности.
    Решение: добавить операторский обзор, provenance и visual QA.
    Метрика: все слайды должны иметь evidence links.
    Следующий шаг: провести hardening renderer/provenance/visual QA."""
    normalized = _normalize_plan_text_for_k1(raw_answer, prompt)
    payload = json.loads(normalized)

    assert payload['deck_title']
    assert len(payload['slides']) == 5
    assert all(slide['title'] for slide in payload['slides'])
    assert all(slide['bullets'] for slide in payload['slides'])
    assert all(slide['slide_type'] for slide in payload['slides'])



def test_rc3_public_response_normalization_always_returns_compact_json() -> None:
    from scripts.kw_rc3_local_gigachat_benchmark_comparison import _normalize_plan_text_for_k1

    prompt = '{"target_slide_count": 5, "deck_goal": "Architecture deck", "source_text": "Gateway accepts documents. Renderer creates slides. Visual QA reviews layout."}'
    messy = "GigaChat plan:\n1. Architecture overview\n2. Runtime modules\n3. Data flow\n4. Risks\n5. Next steps"
    normalized = _normalize_plan_text_for_k1(messy, prompt)
    payload = json.loads(normalized)
    assert isinstance(payload["slides"], list)
    assert len(payload["slides"]) == 5
    assert all(slide["title"] for slide in payload["slides"])
    assert all(slide["bullets"] for slide in payload["slides"])


def test_rc3_public_gigachat_canonical_normalization_handles_architecture_prose() -> None:
    from scripts.kw_rc3_local_gigachat_benchmark_comparison import _normalize_plan_text_for_k1

    prompt = json.dumps(
        {
            "deck_goal": "Create an architecture deck for an offline document-to-slide workflow.",
            "target_slide_count": 7,
            "audience": "senior engineers",
        },
        ensure_ascii=False,
    )
    prose = """
    Архитектура решения: локальное планирование, утверждение плана, рендеринг презентации,
    проверка визуального качества и provenance manifest. Слайд 1: контекст. Слайд 2:
    runtime topology. Слайд 3: renderer quality. Слайд 4: visual QA. Слайд 5: risks.
    """
    payload = json.loads(_normalize_plan_text_for_k1(prose, prompt))
    assert isinstance(payload["deck_title"], str)
    assert len(payload["slides"]) == 7
    for slide in payload["slides"]:
        assert isinstance(slide["title"], str) and slide["title"]
        assert isinstance(slide["bullets"], list) and slide["bullets"]
        assert slide["slide_type"] in {"title", "section", "content", "comparison", "data", "timeline", "conclusion", "appendix"}

