from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

RUNTIME_FOUNDATION_CLOSURE_WORKFLOW_ID = "runtime_foundation.final_closure"
RUNTIME_FOUNDATION_CLOSURE_SCHEMA_VERSION = "runtime_foundation_final_closure.v1"

REQUIRED_RF_CHECKPOINTS: tuple[str, ...] = (
    "RF0", "RF1.1", "RF1.2", "RF1.3", "RF1.4", "RF1.5", "RF1.6", "RF1.7", "RF1.8", "RF1.9", "RF1.10",
    "RF2.0", "RF2.1", "RF2.2", "RF2.2a", "RF2.3", "RF2.4", "RF2.5", "RF2.6", "RF2.7", "RF2_closure",
    "RF3", "RF4",
)

REQUIRED_CLOSURE_FILES: tuple[str, ...] = (
    "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md",
    "docs/codex/RUNTIME_FOUNDATION_FINAL_CLOSURE.md",
    "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md",
    "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md",
    "docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md",
    "docs/codex/GIGACHAT_RUNTIME_HARDENING.md",
    "scripts/kw_runtime_foundation_closure_check.py",
    "scripts/kw_slides_rf2_closure_check.py",
    "scripts/kw_docx_pdf_real_ingestion_check.py",
    "scripts/kw_gigachat_runtime_hardening_check.py",
    "backend/app/services/runtime_foundation_closure.py",
    "backend/app/services/slides_service/rf2_final_closure.py",
    "backend/app/services/docx_service/ingestion.py",
    "backend/app/services/pdf_service/ingestion.py",
    "backend/app/integrations/llm/gigachat_runtime.py",
    "backend/tests/smoke/test_rf_closure_runtime_foundation.py",
    "backend/tests/smoke/test_rf2_closure_slides_runtime.py",
    "backend/tests/smoke/test_rf3_docx_pdf_real_ingestion.py",
    "backend/tests/smoke/test_rf4_gigachat_runtime_hardening.py",
)

REQUIRED_MARKERS: tuple[tuple[str, str], ...] = (
    ("docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md", "RF1"),
    ("docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md", "RF2_closure"),
    ("docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md", "RF3"),
    ("docs/codex/GIGACHAT_RUNTIME_HARDENING.md", "RF4"),
    ("docs/codex/RUNTIME_FOUNDATION_FINAL_CLOSURE.md", "RF_closure"),
    ("docs/codex/RUNTIME_FOUNDATION_FINAL_CLOSURE.md", "K0 is the next phase, but it is not started by RF_closure."),
)

@dataclass(frozen=True)
class RuntimeFoundationClosureReport:
    mode: str
    phase: str
    checkpoint: str
    status: str
    workflow_id: str
    schema_version: str
    required_checkpoints: tuple[str, ...]
    closed_phase_summary: dict[str, bool]
    next_route: tuple[str, ...]
    safe_metadata: dict[str, object]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "phase": self.phase,
            "checkpoint": self.checkpoint,
            "status": self.status,
            "workflow_id": self.workflow_id,
            "schema_version": self.schema_version,
            "required_checkpoints": list(self.required_checkpoints),
            "closed_phase_summary": self.closed_phase_summary,
            "next_route": list(self.next_route),
            "safe_metadata": self.safe_metadata,
            "errors": list(self.errors),
        }


def build_runtime_foundation_closure_report(repo_root: str | Path) -> RuntimeFoundationClosureReport:
    root = Path(repo_root).expanduser().resolve()
    errors: list[str] = []

    for rel in REQUIRED_CLOSURE_FILES:
        if not (root / rel).exists():
            errors.append(f"missing RF_closure required file: {rel}")

    for rel, marker in REQUIRED_MARKERS:
        path = root / rel
        if path.exists() and marker not in path.read_text(encoding="utf-8"):
            errors.append(f"missing RF_closure marker in {rel}: {marker}")

    closed = {
        "rf0_closed": (root / "docs/codex/RUNTIME_FOUNDATION_PHASE_PLAN.md").exists(),
        "rf1_closed": (root / "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md").exists(),
        "rf2_closed": (root / "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md").exists(),
        "rf3_closed": (root / "docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md").exists(),
        "rf4_closed": (root / "docs/codex/GIGACHAT_RUNTIME_HARDENING.md").exists(),
    }
    for name, value in closed.items():
        if not value:
            errors.append(f"{name} is not closed")

    runtime_foundation_closed = not errors and all(closed.values())
    safe_metadata: dict[str, object] = {
        "workflow_id": RUNTIME_FOUNDATION_CLOSURE_WORKFLOW_ID,
        "schema_version": RUNTIME_FOUNDATION_CLOSURE_SCHEMA_VERSION,
        "runtime_foundation_closed": runtime_foundation_closed,
        "rf0_closed": closed["rf0_closed"],
        "rf1_closed": closed["rf1_closed"],
        "rf2_closed": closed["rf2_closed"],
        "rf3_closed": closed["rf3_closed"],
        "rf4_closed": closed["rf4_closed"],
        "rf_closure_ready_for_k0": runtime_foundation_closed,
        "k_phase_started_by_rf_closure": False,
        "k_phase_ready_to_start_after_rf_closure": runtime_foundation_closed,
        "next_recommended_step": "K0 — Kimi-level rubric and golden deck benchmark",
        "runtime_changed_by_rf_closure": False,
        "dependency_versions_changed_by_rf_closure": False,
        "dockerfiles_changed_by_rf_closure": False,
        "frontend_runtime_changed_by_rf_closure": False,
        "llm_topology_changed_by_rf_closure": False,
        "api_endpoint_added_by_rf_closure": False,
        "db_schema_migration_added_by_rf_closure": False,
        "queue_or_event_store_migration_added_by_rf_closure": False,
        "visual_qa_runtime_added_by_rf_closure": False,
        "cloud_llm_added_by_rf_closure": False,
        "cloud_ocr_added_by_rf_closure": False,
        "npm_audit_fix_force_run_by_rf_closure": False,
        "whole_project_kimi_level_supported": False,
    }

    return RuntimeFoundationClosureReport(
        mode="runtime-foundation-final-closure",
        phase="Runtime Foundation",
        checkpoint="RF_closure",
        status="ready" if runtime_foundation_closed else "failed",
        workflow_id=RUNTIME_FOUNDATION_CLOSURE_WORKFLOW_ID,
        schema_version=RUNTIME_FOUNDATION_CLOSURE_SCHEMA_VERSION,
        required_checkpoints=REQUIRED_RF_CHECKPOINTS,
        closed_phase_summary=closed,
        next_route=("K0", "K1", "K2", "K3", "K4", "K5", "K6"),
        safe_metadata=safe_metadata,
        errors=tuple(errors),
    )
