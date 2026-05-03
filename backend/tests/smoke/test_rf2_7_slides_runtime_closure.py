from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.slides_service.runtime_closure import (
    RF2_SLIDES_RUNTIME_NEXT_ROUTE,
    build_slides_runtime_closure_readiness,
    validate_slides_runtime_closure_readiness,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_runtime_closure_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf2_7_checker_reports_ready_closure_gate() -> None:
    result = run_check("--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "slides-runtime-rf2-closure-readiness"
    assert payload["checkpoint"] == "RF2.7"
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["rf2_slides_path_ready_for_closure"] is True
    assert payload["runtime_changed_by_rf2_7"] is False
    assert payload["dependency_versions_changed_by_rf2_7"] is False
    assert payload["dockerfiles_changed_by_rf2_7"] is False
    assert payload["api_endpoint_added_by_rf2_7"] is False
    assert payload["db_schema_migration_added_by_rf2_7"] is False
    assert payload["visual_qa_runtime_added_by_rf2_7"] is False
    assert payload["k_phase_started_by_rf2_7"] is False


def test_rf2_7_runtime_closure_readiness_contract_preserves_route_and_non_goals() -> None:
    readiness = build_slides_runtime_closure_readiness()
    errors = validate_slides_runtime_closure_readiness(readiness)

    assert errors == []
    assert readiness.closed_checkpoints == (
        "RF2.0",
        "RF2.1",
        "RF2.2",
        "RF2.2a",
        "RF2.3",
        "RF2.4",
        "RF2.5",
        "RF2.6",
    )
    assert readiness.next_route == RF2_SLIDES_RUNTIME_NEXT_ROUTE
    assert readiness.next_route[0] == "RF2_closure"
    assert readiness.next_route[-1] == "K0"
    assert readiness.rf2_slides_path_ready_for_closure is True
    assert readiness.k_phase_ready_to_start is False
    assert readiness.kimi_grade_supported is False
    assert readiness.whole_project_kimi_level_supported is False


def test_rf2_7_runtime_smoke_links_generation_retry_render_mode_and_provenance() -> None:
    result = run_check("--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    smoke = payload["runtime_smoke"]

    assert smoke["status"] == "ready"
    assert smoke["rf2_slides_path_ready_for_closure"] is True
    assert smoke["generation_provenance_supported"] is True
    assert smoke["retry_provenance_supported"] is True
    assert smoke["generation_manifest_links_pptx_artifact"] is True
    assert smoke["retry_manifest_links_pptx_artifact"] is True
    assert smoke["retry_parent_links_present"] is True
    assert smoke["render_mode_runtime_hardened"] is True
    assert smoke["k_phase_ready_to_start"] is False
    assert smoke["kimi_grade_supported"] is False
    assert smoke["whole_project_kimi_level_supported"] is False


def test_rf2_7_production_readiness_gate_mentions_closure_check() -> None:
    gate = (repo_root() / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")

    assert "Slides RF2 runtime closure and readiness" in gate
    assert "scripts/kw_slides_runtime_closure_check.py" in gate
    assert "docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md" in gate
    assert "backend/tests/smoke/test_rf2_7_slides_runtime_closure.py" in gate
