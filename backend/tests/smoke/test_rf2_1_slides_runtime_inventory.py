from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_runtime_inventory_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_1_inventory_check_is_ready_and_does_not_overclaim_kimi() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-runtime-capability-inventory"
    assert payload["phase"] == "RF2"
    assert payload["checkpoint"] == "RF2.1"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf2_1"] is False
    assert payload["dependency_versions_changed_by_rf2_1"] is False
    assert payload["dockerfiles_changed_by_rf2_1"] is False
    assert payload["llm_topology_changed_by_rf2_1"] is False
    assert payload["browser_runtime_changed_by_rf2_1"] is False
    assert payload["frontend_runtime_changed_by_rf2_1"] is False
    assert payload["current_generator_grade"] == "baseline_deterministic_not_kimi_grade"
    assert payload["product_loop_grade"] == "baseline_inventory_not_kimi_level_project"
    assert payload["kimi_grade_supported"] is False
    assert payload["product_grade_supported"] is False
    assert payload["whole_project_kimi_level_supported"] is False
    assert "renderer_layout_quality_not_kimi_grade" in payload["system_quality_gaps"]
    assert payload["status"] == "ready"
    assert payload["errors"] == []


def test_rf2_1_baseline_smoke_generates_valid_pptx_but_not_product_grade_claim() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    smoke = payload["baseline_smoke"]

    assert smoke["status"] == "ready"
    assert smoke["payload_starts_with_pk"] is True
    assert smoke["payload_size_bytes"] > 0
    assert smoke["slide_count"] >= 5
    assert smoke["slide_xml_count"] == smoke["slide_count"]
    assert smoke["template_id"] == "business_clean"
    assert smoke["media_entry_count"] >= 1
    assert smoke["has_media_assets_in_plan"] is True
    assert smoke["has_source_grounding_metadata"] is True
    assert smoke["current_generator_grade"] == "baseline_deterministic_not_kimi_grade"
    assert smoke["product_loop_grade"] == "baseline_inventory_not_kimi_level_project"
    assert smoke["kimi_grade_supported"] is False
    assert smoke["product_grade_supported"] is False
    assert smoke["whole_project_kimi_level_supported"] is False
    assert smoke["approved_plan_runtime_proven"] is False
    assert smoke["provenance_artifact_emitted"] is False
    assert smoke["persistent_task_event_stream_proven"] is False
    assert "[Content_Types].xml" in smoke["core_parts_present"]
    assert "ppt/presentation.xml" in smoke["core_parts_present"]


def test_rf2_1_capability_summary_has_baseline_partial_gap_and_contract_buckets() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    capabilities = {item["capability_id"]: item for item in payload["capabilities"]}

    assert capabilities["deterministic_pptx_generation_from_source_text"]["status"] == "baseline_runtime_ready"
    assert capabilities["local_templates_and_layouts"]["status"] == "baseline_runtime_ready"
    assert capabilities["presentation_catalog_and_plan_read_api"]["status"] == "baseline_runtime_ready"
    assert capabilities["frontend_plan_editor_surface"]["status"] == "baseline_runtime_ready"
    assert capabilities["approved_plan_generation_path"]["status"] == "partial_runtime"
    assert capabilities["plan_snapshot_and_retry_lifecycle"]["status"] == "partial_runtime"
    assert capabilities["kimi_grade_slides_quality"]["status"] == "product_gap"
    assert capabilities["product_grade_layout_quality"]["status"] == "product_gap"
    assert capabilities["slides_provenance_manifest_artifact"]["status"] == "contract_only"

    assert payload["summary"]["baseline_runtime_ready"] >= 4
    assert payload["summary"]["partial_runtime"] >= 3
    assert payload["summary"]["product_gap"] >= 3
    assert payload["summary"]["contract_only"] >= 4
    assert payload["next_recommended_step"] == "RF2.2 — Minimal deterministic PPTX generation from approved plan"


def test_rf2_1_marker_report_covers_runtime_surfaces_and_deterministic_planner_limits() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    markers = payload["marker_report"]

    for marker in (
        "outline_deterministic_segment_split",
        "outline_bounded_bullets",
        "slides_service_generate_deck",
        "slides_service_returns_transform_output",
        "entrypoint_generate",
        "pptx_from_plan",
        "presentation_list_route",
        "presentation_versions_route",
        "presentation_current_plan_route",
        "presentation_version_plan_route",
        "presentation_plan_diff_route",
        "plan_snapshot_service",
        "deck_revision_service",
        "frontend_presentations_api",
        "frontend_plan_editor",
        "frontend_plan_editor_e2e",
        "service_test_openxml",
    ):
        assert markers[marker] is True


def test_rf2_1_inventory_doc_preserves_handoff_non_goals_and_no_kimi_overclaim() -> None:
    doc = (repo_root() / "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md").read_text(encoding="utf-8")

    assert "RF2.1 checkpoint" in doc
    assert "Critical interpretation rule" in doc
    assert "Whole-project Kimi-level rule" in doc
    assert "Kimi-level target applies to the whole slides product loop" in doc
    assert "not enough to claim that KW Studio works at the level of Kimi slides" in doc
    assert "Baseline runtime that is currently present" in doc
    assert "Partial runtime baseline" in doc
    assert "Product-quality gaps" in doc
    assert "Contract-only or not-yet-runtime RF2 work" in doc
    assert "Kimi-grade support remains explicitly false" in doc
    assert "RF2.2 — Minimal deterministic PPTX generation from approved plan" in doc
    assert "do not overclaim Kimi-level output until real product-quality gates exist" in doc
    assert "do not run `npm audit fix --force`" in doc


def test_rf2_1_production_readiness_gate_mentions_inventory() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides runtime capability inventory and baseline smoke" in gate
    assert "scripts/kw_slides_runtime_inventory_check.py" in gate
    assert "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md" in gate
    assert "backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py" in gate
