from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

K0_CHECKPOINT = "K0"
K_PHASE_BRANCH = "8_K_Phase"
RF_CLOSURE_BASE_COMMIT = "a52f038b0fb651e3b33c33f999ca9ba0d615bff9"
KIMI_LEVEL_PASS_SCORE = 85
CRITICAL_DIMENSION_FLOOR = 75

QUALITY_DIMENSIONS: tuple[dict[str, object], ...] = (
    {"dimension_id": "storyline_quality", "title": "Storyline quality", "weight": 12, "k0_measure": "Narrative arc, slide order, executive takeaway, and section logic.", "minimum_kimi_candidate_score": 85, "critical": True},
    {"dimension_id": "slide_hierarchy", "title": "Slide hierarchy", "weight": 10, "k0_measure": "One clear message per slide with title/body hierarchy and emphasis.", "minimum_kimi_candidate_score": 80, "critical": True},
    {"dimension_id": "layout_consistency", "title": "Layout consistency", "weight": 10, "k0_measure": "Templates, spacing, alignment, recurring structures, and visual rhythm.", "minimum_kimi_candidate_score": 80, "critical": True},
    {"dimension_id": "visual_density_control", "title": "Visual density control", "weight": 8, "k0_measure": "Readable density with appropriate slide splitting.", "minimum_kimi_candidate_score": 80, "critical": False},
    {"dimension_id": "source_faithfulness", "title": "Source faithfulness", "weight": 12, "k0_measure": "Deck claims are traceable to sources without hallucinated facts.", "minimum_kimi_candidate_score": 90, "critical": True},
    {"dimension_id": "editability", "title": "Editability", "weight": 8, "k0_measure": "Plan, slide intent, render mode, and retry instructions remain operator-editable.", "minimum_kimi_candidate_score": 80, "critical": False},
    {"dimension_id": "retry_quality", "title": "Retry quality", "weight": 8, "k0_measure": "Retry preserves lineage, applies intent, and improves target issue without regression.", "minimum_kimi_candidate_score": 80, "critical": False},
    {"dimension_id": "visual_qa_result", "title": "Visual QA result", "weight": 8, "k0_measure": "Overflow, contrast, reading order, and layout defects are detected.", "minimum_kimi_candidate_score": 80, "critical": False},
    {"dimension_id": "provenance_quality", "title": "Provenance quality", "weight": 12, "k0_measure": "Artifact, plan, source, event, retry, and manifest links are complete and safe-redacted.", "minimum_kimi_candidate_score": 90, "critical": True},
    {"dimension_id": "offline_reproducibility", "title": "Offline reproducibility", "weight": 12, "k0_measure": "Runs without public internet, cloud fallback, or uncontrolled dependency/runtime changes.", "minimum_kimi_candidate_score": 90, "critical": True},
)

GOLDEN_BENCHMARK_CASES: tuple[dict[str, object], ...] = (
    {"case_id": "k0_exec_memo_to_board_deck", "title": "Source memo to executive deck", "source_kind": "memo", "target_deck_type": "executive_decision_deck", "target_slide_count_range": [7, 10], "required_capabilities": ["source_intake", "storyline", "executive_summary", "provenance_manifest", "retry"], "evaluation_focus": ["storyline_quality", "source_faithfulness", "slide_hierarchy"]},
    {"case_id": "k0_arch_doc_to_architecture_deck", "title": "Technical document to architecture deck", "source_kind": "technical_document", "target_deck_type": "architecture_review_deck", "target_slide_count_range": [8, 12], "required_capabilities": ["docx_pdf_ingestion", "architecture_story", "diagram_intent", "provenance_manifest"], "evaluation_focus": ["source_faithfulness", "layout_consistency", "visual_density_control"]},
    {"case_id": "k0_project_log_to_status_deck", "title": "Project log to status deck", "source_kind": "project_log", "target_deck_type": "status_update_deck", "target_slide_count_range": [6, 9], "required_capabilities": ["timeline_synthesis", "risk_summary", "next_actions", "retry"], "evaluation_focus": ["storyline_quality", "editability", "retry_quality"]},
    {"case_id": "k0_comparison_table_to_decision_deck", "title": "Comparison table to decision deck", "source_kind": "comparison_table", "target_deck_type": "decision_deck", "target_slide_count_range": [6, 8], "required_capabilities": ["table_understanding", "tradeoff_synthesis", "recommendation", "source_traceability"], "evaluation_focus": ["slide_hierarchy", "visual_density_control", "source_faithfulness"]},
    {"case_id": "k0_long_docx_pdf_to_structured_presentation", "title": "Long DOCX/PDF to structured presentation", "source_kind": "long_docx_pdf", "target_deck_type": "structured_explainer_deck", "target_slide_count_range": [10, 14], "required_capabilities": ["real_docx_pdf_ingestion", "source_grounding", "sectioning", "visual_qa", "provenance_manifest"], "evaluation_focus": ["source_faithfulness", "provenance_quality", "offline_reproducibility"]},
)

ACCEPTANCE_GATES: tuple[dict[str, object], ...] = (
    {"gate_id": "k0_no_premature_kimi_claim", "required": True, "rule": "K0 defines the rubric and benchmark only; it must not claim KW Studio already reaches Kimi-level."},
    {"gate_id": "k0_weighted_score_threshold", "required": True, "rule": "A future Kimi-level candidate run must reach overall weighted score >= 85."},
    {"gate_id": "k0_critical_dimension_floor", "required": True, "rule": "Every critical dimension must meet its configured minimum."},
    {"gate_id": "k0_offline_reproducibility", "required": True, "rule": "Benchmark execution must preserve offline/intranet mode and direct local GigaChat-first topology."},
    {"gate_id": "k0_artifact_provenance_required", "required": True, "rule": "Every benchmark output must include artifact history and source-to-artifact provenance evidence."},
)

@dataclass(frozen=True)
class K0RubricReport:
    mode: str
    checkpoint: str
    branch: str
    rf_closure_base_commit: str
    status: str
    k_phase_started_by_k0: bool
    k0_rubric_defined: bool
    golden_benchmark_defined: bool
    kimi_level_claimed_by_k0: bool
    whole_project_kimi_level_supported: bool
    runtime_changed_by_k0: bool
    dependency_versions_changed_by_k0: bool
    dockerfiles_changed_by_k0: bool
    api_endpoint_added_by_k0: bool
    db_schema_migration_added_by_k0: bool
    rubric_dimensions: tuple[dict[str, object], ...]
    golden_benchmark_cases: tuple[dict[str, object], ...]
    acceptance_gates: tuple[dict[str, object], ...]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

def validate_k0_rubric() -> list[str]:
    errors: list[str] = []
    dimension_ids = [str(item.get("dimension_id")) for item in QUALITY_DIMENSIONS]
    if len(QUALITY_DIMENSIONS) != 10:
        errors.append("K0 must define exactly 10 rubric dimensions.")
    if len(set(dimension_ids)) != len(dimension_ids):
        errors.append("K0 rubric dimension ids must be unique.")
    weight_sum = sum(int(item.get("weight", 0)) for item in QUALITY_DIMENSIONS)
    if weight_sum != 100:
        errors.append(f"K0 rubric weights must sum to 100, got {weight_sum}.")
    critical_ids = {str(item.get("dimension_id")) for item in QUALITY_DIMENSIONS if bool(item.get("critical"))}
    required_critical = {"storyline_quality", "slide_hierarchy", "layout_consistency", "source_faithfulness", "provenance_quality", "offline_reproducibility"}
    missing_critical = sorted(required_critical - critical_ids)
    if missing_critical:
        errors.append(f"K0 missing critical dimensions: {missing_critical}")
    if len(GOLDEN_BENCHMARK_CASES) != 5:
        errors.append("K0 must define exactly 5 golden benchmark cases.")
    case_ids = [str(item.get("case_id")) for item in GOLDEN_BENCHMARK_CASES]
    if len(set(case_ids)) != len(case_ids):
        errors.append("K0 benchmark case ids must be unique.")
    required_sources = {"memo", "technical_document", "project_log", "comparison_table", "long_docx_pdf"}
    actual_sources = {str(item.get("source_kind")) for item in GOLDEN_BENCHMARK_CASES}
    missing_sources = sorted(required_sources - actual_sources)
    if missing_sources:
        errors.append(f"K0 missing golden benchmark source kinds: {missing_sources}")
    if any(not bool(gate.get("required")) for gate in ACCEPTANCE_GATES):
        errors.append("All K0 acceptance gates must be required.")
    return errors

def build_k0_rubric_report() -> K0RubricReport:
    errors = validate_k0_rubric()
    return K0RubricReport(
        mode="k0-kimi-level-rubric-golden-benchmark",
        checkpoint=K0_CHECKPOINT,
        branch=K_PHASE_BRANCH,
        rf_closure_base_commit=RF_CLOSURE_BASE_COMMIT,
        status="ready" if not errors else "failed",
        k_phase_started_by_k0=True,
        k0_rubric_defined=not errors,
        golden_benchmark_defined=not errors,
        kimi_level_claimed_by_k0=False,
        whole_project_kimi_level_supported=False,
        runtime_changed_by_k0=False,
        dependency_versions_changed_by_k0=False,
        dockerfiles_changed_by_k0=False,
        api_endpoint_added_by_k0=False,
        db_schema_migration_added_by_k0=False,
        rubric_dimensions=QUALITY_DIMENSIONS,
        golden_benchmark_cases=GOLDEN_BENCHMARK_CASES,
        acceptance_gates=ACCEPTANCE_GATES,
        errors=tuple(errors),
    )

def score_candidate_dimension_scores(scores: dict[str, int]) -> dict[str, object]:
    errors: list[str] = []
    weighted_total = 0.0
    for dimension in QUALITY_DIMENSIONS:
        dimension_id = str(dimension["dimension_id"])
        if dimension_id not in scores:
            errors.append(f"missing score for {dimension_id}")
            continue
        value = int(scores[dimension_id])
        if value < 0 or value > 100:
            errors.append(f"score for {dimension_id} must be between 0 and 100")
            continue
        weighted_total += value * int(dimension["weight"]) / 100
        minimum = int(dimension["minimum_kimi_candidate_score"])
        if value < minimum:
            errors.append(f"{dimension_id} below minimum {minimum}: {value}")
    passed = not errors and weighted_total >= KIMI_LEVEL_PASS_SCORE
    return {"weighted_total": round(weighted_total, 2), "kimi_level_candidate_passed": passed, "kimi_level_claimed": False, "errors": errors}
