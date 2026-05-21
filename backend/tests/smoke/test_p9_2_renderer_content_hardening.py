from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine

GENERIC_LABELS = ("K1 Plan", "Key point", "Additional source-grounded planning point")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_cases() -> list[dict[str, object]]:
    return json.loads((repo_root() / "backend/tests/fixtures/k_phase/rc1_golden_benchmark_cases.json").read_text(encoding="utf-8"))


def case_by_id(case_id: str) -> dict[str, object]:
    return next(case for case in load_cases() if case["case_id"] == case_id)


def build_plan(case_id: str):
    case = case_by_id(case_id)
    result = LocalGigaChatPlanningEngine(None).plan(
        K1PlanningRequest(
            source_text=str(case["source_text"]),
            audience=str(case.get("audience") or "operator_review"),
            deck_goal=str(case.get("deck_goal") or "Create a source-grounded presentation plan."),
            target_slide_count=int(case.get("target_slide_count") or 7),
            source_refs=({"source_id": case_id, "title": str(case.get("title") or case_id)},),
        )
    )
    return result


def plan_text(result) -> str:
    parts = [result.plan.deck_title]
    for slide in result.plan.slides:
        parts.append(slide.title)
        parts.extend(slide.bullets)
    return "\n".join(parts)


def assert_no_generic_labels(text: str) -> None:
    lowered = text.lower()
    for label in GENERIC_LABELS:
        assert label.lower() not in lowered


def test_p9_2_checker_reports_ready(tmp_path: Path) -> None:
    root = repo_root()
    artifacts_dir = tmp_path / "p9-2"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_p9_2_renderer_content_hardening_check.py",
            "--repo-root",
            str(root),
            "--artifacts-dir",
            str(artifacts_dir),
            "--require-ready",
            "--json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "P9-2"
    assert payload["status"] == "ready"
    assert payload["case_probe_count"] == 5
    assert payload["generic_fallback_labels_removed"] is True
    assert payload["comparison_table_decision_matrix_supported"] is True
    assert payload["project_log_late_phase_coverage_supported"] is True
    assert payload["long_source_filler_slide_prevention_supported"] is True
    assert payload["human_review_findings_addressed_by_p9_2"] is True
    assert payload["kimi_level_claimed_by_p9_2"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert payload["api_endpoint_added_by_p9_2"] is False
    assert payload["db_schema_migration_added_by_p9_2"] is False
    assert payload["frontend_runtime_changed_by_p9_2"] is False
    assert payload["dependency_versions_changed_by_p9_2"] is False
    assert payload["dockerfiles_changed_by_p9_2"] is False
    assert payload["cloud_llm_added_by_p9_2"] is False
    assert payload["cloud_vision_added_by_p9_2"] is False
    assert (artifacts_dir / "p9-2-renderer-content-hardening.json").exists()


def test_p9_2_removes_generic_fallback_labels_across_golden_cases() -> None:
    for case in load_cases():
        result = build_plan(str(case["case_id"]))
        text = plan_text(result)
        assert_no_generic_labels(text)
        assert result.safe_metadata["p9_2_renderer_content_hardening_supported"] is True
        assert result.safe_metadata["generic_fallback_labels_removed"] is True
        assert result.safe_metadata["human_review_findings_addressed_by_p9_2"] is True
        assert result.safe_metadata["kimi_level_claimed_by_k1"] is False
        assert result.safe_metadata["whole_project_kimi_level_supported"] is False


def test_p9_2_comparison_table_becomes_decision_matrix() -> None:
    result = build_plan("k0_comparison_table_to_decision_deck")
    text = plan_text(result)
    assert result.safe_metadata["source_profile"] == "comparison_table"
    assert result.safe_metadata["comparison_table_decision_matrix_supported"] is True
    assert "Decision matrix" in text
    assert "Recommended default" in text
    assert "Rejected default" in text
    assert "Direct local GigaChat" in text
    assert "LiteLLM" in text
    assert "Cloud LLM" in text


def test_p9_2_project_log_covers_late_phase_closure_risks_and_next_action() -> None:
    result = build_plan("k0_project_log_to_status_deck")
    text = plan_text(result)
    assert result.safe_metadata["source_profile"] == "project_log"
    assert result.safe_metadata["project_log_late_phase_coverage_supported"] is True
    for expected in ("K4", "K5", "K6", "closure", "Current risks", "Next action", "RC1"):
        assert expected.lower() in text.lower()


def test_p9_2_long_structured_source_has_meaningful_late_slides() -> None:
    result = build_plan("k0_long_docx_pdf_to_structured_presentation")
    text = plan_text(result)
    late_text = "\n".join(slide.title + "\n" + "\n".join(slide.bullets) for slide in result.plan.slides[-2:])
    assert result.safe_metadata["source_profile"] == "long_structured_source"
    assert result.safe_metadata["long_source_filler_slide_prevention_supported"] is True
    assert len(result.plan.slides) == 10
    assert_no_generic_labels(text)
    for expected in ("Product goal", "Offline constraint", "LLM topology", "Runtime Foundation", "K-phase", "Benchmark requirements", "Release risks", "RC1"):
        assert expected.lower() in text.lower()
    assert any(token.lower() in late_text.lower() for token in ("Evidence package", "Claim guard", "human review", "PPTX", "manifest"))
