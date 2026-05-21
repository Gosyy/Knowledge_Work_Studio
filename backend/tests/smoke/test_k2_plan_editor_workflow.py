from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.services.k_phase.local_gigachat_planner import K1PlanningRequest, LocalGigaChatPlanningEngine
from backend.app.services.k_phase.plan_editor import (
    K2EvidenceLink,
    K2PlanEditRequest,
    K2PlanEditorError,
    K2PlanEditorWorkflow,
    K2SlidePatch,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_k2_plan_editor_check.py", "--repo-root", str(root), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sample_plan():
    return LocalGigaChatPlanningEngine(None).plan(
        K1PlanningRequest(
            source_text="Revenue grew. Churn risk increased. Retention automation is recommended. Evidence must stay linked.",
            target_slide_count=5,
        )
    ).plan


def test_k2_checker_reports_ready_without_kimi_overclaim() -> None:
    result = run_check("--require-ready", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["checkpoint"] == "K2"
    assert payload["status"] == "ready"
    assert payload["runtime_changed_by_k2"] is True
    assert payload["api_endpoint_added_by_k2"] is False
    assert payload["db_schema_migration_added_by_k2"] is False
    assert payload["frontend_runtime_changed_by_k2"] is False
    assert payload["kimi_level_claimed_by_k2"] is False
    assert payload["whole_project_kimi_level_supported"] is False


def test_k2_plan_editor_blocks_generation_until_approved() -> None:
    workflow = K2PlanEditorWorkflow()
    created = workflow.create_session(sample_plan())
    try:
        workflow.to_presentation_plan(created.session)
    except K2PlanEditorError:
        pass
    else:
        raise AssertionError("K2 must require approval before conversion to PresentationPlan")


def test_k2_plan_editor_applies_slide_intent_evidence_render_mode_and_approval() -> None:
    workflow = K2PlanEditorWorkflow()
    created = workflow.create_session(sample_plan())
    slide = created.session.slides[0]
    edited = workflow.apply_edits(
        created.session,
        K2PlanEditRequest(
            patches=(
                K2SlidePatch(
                    slide_id=slide.slide_id,
                    title="Operator-approved opening",
                    bullets=("Retention is the priority", "Evidence remains linked"),
                    slide_intent="Make the operator decision explicit.",
                    evidence_links=(K2EvidenceLink(source_id="memo_001", title="Q1 memo", locator="p1"),),
                    visual_intent="process_visual",
                    layout_hint="content_with_visual",
                ),
            ),
            change_summary="Attach source evidence and clarify the opening slide.",
            requested_render_mode="template",
            template_id="business_clean",
        ),
    )
    approved = workflow.approve(workflow.request_approval(edited.session).session)
    assert approved.approved_plan is not None
    assert approved.approved_plan.slides[0].title == "Operator-approved opening"
    assert approved.safe_metadata["approval_required_before_generation"] is True
    assert approved.safe_metadata["render_mode"] == "template"
    assert approved.safe_metadata["template_id"] == "business_clean"
    assert tuple(approved.safe_metadata["event_types"])[-1] == "k2.plan_editor.approved"


def test_k2_rejects_template_without_template_id_and_unknown_slide() -> None:
    workflow = K2PlanEditorWorkflow()
    plan = sample_plan()
    try:
        workflow.create_session(plan, render_mode="template")
    except K2PlanEditorError:
        pass
    else:
        raise AssertionError("K2 template mode must require explicit template_id")
    session = workflow.create_session(plan).session
    try:
        workflow.apply_edits(session, K2PlanEditRequest(patches=(K2SlidePatch(slide_id="missing", title="x"),), change_summary="bad"))
    except K2PlanEditorError:
        pass
    else:
        raise AssertionError("K2 must reject edits for unknown slide_id")
