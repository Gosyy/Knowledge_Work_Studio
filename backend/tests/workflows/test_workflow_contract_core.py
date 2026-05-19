from __future__ import annotations

from backend.app.workflows.core_contracts import (
    MANDATORY_PRODUCT_WORKFLOW_IDS,
    get_workflow_contract_core,
    validate_workflow_contract_core,
    workflow_contract_core_report,
)


def test_kr4a_contract_core_contains_all_mandatory_product_workflows() -> None:
    report = workflow_contract_core_report()

    assert report["status"] == "ready", report["errors"]
    assert set(report["contracts"]) == set(MANDATORY_PRODUCT_WORKFLOW_IDS)
    assert set(MANDATORY_PRODUCT_WORKFLOW_IDS) == {
        "docx",
        "pdf",
        "xlsx",
        "slides",
        "python_analysis",
        "browser_evidence",
    }
    assert validate_workflow_contract_core() == []


def test_kr4a_every_workflow_has_manifest_quality_and_provenance() -> None:
    for workflow_id in MANDATORY_PRODUCT_WORKFLOW_IDS:
        contract = get_workflow_contract_core(workflow_id)
        artifact_names = {artifact.name for artifact in contract.artifacts}

        assert contract.workflow_input.offline_input_ready is True
        assert contract.run.offline_ready is True
        assert contract.plan.operator_editable is True
        assert contract.manifest.records_artifact_history is True
        assert contract.manifest.records_restore_metadata is True
        assert contract.quality.must_fail_closed is True
        assert contract.provenance.evidence_required is True
        assert "artifact_manifest.json" in artifact_names
        assert "source_evidence_manifest.json" in artifact_names


def test_kr4a_xlsx_contract_is_first_class_not_optional() -> None:
    xlsx = get_workflow_contract_core("xlsx")
    artifact_names = {artifact.name for artifact in xlsx.artifacts}

    assert "xlsx" in xlsx.workflow_input.source_kinds
    assert "csv" in xlsx.workflow_input.source_kinds
    assert "workbook_manifest.json" in artifact_names
    assert "formula_inventory.json" in artifact_names
    assert "table_previews/*.csv" in artifact_names
    assert "workbook_range_to_artifact" == xlsx.provenance.traceability_level


def test_kr4a_slides_contract_requires_independent_render_and_citations() -> None:
    slides = get_workflow_contract_core("slides")
    artifact_names = {artifact.name for artifact in slides.artifacts}

    assert "slide_plan.json" == slides.plan.plan_artifact
    assert "independent_rendered_slides/*.png" in artifact_names
    assert "citation_manifest.json" in artifact_names
    assert "visual_qa_report.json" in artifact_names
    assert slides.provenance.citation_manifest == "citation_manifest.json"
