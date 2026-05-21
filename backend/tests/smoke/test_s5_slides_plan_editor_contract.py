from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_s5_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/kw_slides_plan_editor_check.py", "--repo-root", str(REPO_ROOT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_s5_required_files_exist() -> None:
    required = (
        "frontend/src/components/presentations/slides-plan-editor-panel.tsx",
        "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts",
        "docs/slides-plan-editor-ui.md",
        "scripts/kw_slides_plan_editor_check.py",
    )
    for relative in required:
        assert (REPO_ROOT / relative).is_file(), relative


def test_s5_component_exposes_plan_first_controls() -> None:
    text = (REPO_ROOT / "frontend/src/components/presentations/slides-plan-editor-panel.tsx").read_text(encoding="utf-8")
    for marker in (
        "Slides plan editor",
        "Plan editor presentation id",
        "Editable deck title",
        "Template mode",
        "Save editable plan draft",
        "Prepare retry from saved plan",
        "slides.retry.from_saved_plan.requested",
    ):
        assert marker in text


def test_s5_workspace_shell_renders_plan_editor() -> None:
    text = (REPO_ROOT / "frontend/src/components/layout/workspace-shell.tsx").read_text(encoding="utf-8")
    assert "SlidesPlanEditorPanel" in text
    assert "slides-plan-editor-panel" in text


def test_s5_e2e_covers_edit_and_retry_preview() -> None:
    text = (REPO_ROOT / "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts").read_text(encoding="utf-8")
    assert "slides plan editor edits saved plan and prepares retry payload" in text
    assert "Edited analysis from saved plan" in text
    assert "slides.retry.from_saved_plan.requested" in text


def test_s5_documentation_captures_scope_controls() -> None:
    text = (REPO_ROOT / "docs/slides-plan-editor-ui.md").read_text(encoding="utf-8").lower()
    for marker in ("s5", "editable plan", "retry from saved plan", "adaptive", "template", "offline"):
        assert marker in text


def test_s5_cli_reports_ready_json() -> None:
    result = run_s5_check("--json", "--require-ready")
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout.split("[PASS]")[0])
    assert report["status"] == "ready"
    assert report["component_marker_count"] >= 8


def test_s5_production_gate_runs_plan_editor_check() -> None:
    text = (REPO_ROOT / "scripts/kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "scripts/kw_slides_plan_editor_check.py" in text
    assert "Slides plan editor UI contract" in text

def test_s5_plan_editor_component_uses_escaped_newline_join_and_split() -> None:
    component = REPO_ROOT / "frontend/src/components/presentations/slides-plan-editor-panel.tsx"
    text = component.read_text(encoding="utf-8")
    assert 'slide.bullets.join("\\n")' in text
    assert '.split("\\n")' in text
    assert 'slide.bullets.join("\\\\n")' not in text
    assert '.split("\\\\n")' not in text

def test_s5_plan_editor_component_and_e2e_use_escaped_newline_literals() -> None:
    component = REPO_ROOT / "frontend/src/components/presentations/slides-plan-editor-panel.tsx"
    component_text = component.read_text(encoding="utf-8")
    assert 'slide.bullets.join("\\n")' in component_text
    assert '.split("\\n")' in component_text
    assert 'slide.bullets.join("\n")' not in component_text
    assert '.split("\n")' not in component_text

    e2e = REPO_ROOT / "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts"
    e2e_text = e2e.read_text(encoding="utf-8")
    assert 'fill("Preserve saved plan provenance\\nRetry only after operator review")' in e2e_text
    assert 'fill("Preserve saved plan provenance\nRetry only after operator review")' not in e2e_text
