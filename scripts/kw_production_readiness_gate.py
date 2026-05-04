#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

REQUIRED_P_PHASE_FILES = (
    "P_PHASE_ISSUE_PACK.md",
    "P_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
    ".github/workflows/postgres-integration.yml",
    ".github/workflows/frontend-e2e-smoke.yml",
    "scripts/kw_postgres_integration_gate.py",
    "scripts/kw_validate_deployment_package.py",
    "scripts/kw_schema_preflight.py",
    "scripts/kw_deployment_preflight.py",
    "scripts/kw_runtime_diagnostics.py",
    "scripts/kw_llm_topology_check.py",
    "scripts/kw_litellm_gateway_check.py",
    "scripts/kw_visual_qa_planning_check.py",
    "scripts/kw_offline_dependency_inventory_check.py", "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_MANIFEST.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md",
    "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md",
    "docs/codex/OFFLINE_BOOTSTRAP_INTEGRITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_ARTIFACT_INVENTORY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUILD_READINESS.md",
    "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md",
    "docs/codex/SLIDES_RUNTIME_PHASE_PLAN.md",
    "docs/codex/SLIDES_RUNTIME_CAPABILITY_INVENTORY.md",
    "docs/codex/SLIDES_APPROVED_PLAN_RUNTIME.md",
    "docs/codex/SLIDES_APPROVED_PLAN_LIFECYCLE_RUNTIME.md",
    "docs/codex/SLIDES_SAVED_PLAN_RETRY_RUNTIME.md",
    "backend/app/services/slides_service/saved_plan_retry.py",
    "scripts/kw_slides_saved_plan_retry_check.py",
    "backend/tests/smoke/test_rf2_4_slides_saved_plan_retry.py",
    "docs/codex/SLIDES_RENDER_MODE_RUNTIME_HARDENING.md",
    "docs/codex/SLIDES_PROVENANCE_MANIFEST_RUNTIME.md",
    "docs/codex/SLIDES_RUNTIME_RF2_CLOSURE.md",
    "docs/codex/SLIDES_RUNTIME_RF2_FINAL_CLOSURE.md",
    "backend/app/services/slides_service/rf2_final_closure.py",
    "scripts/kw_slides_rf2_closure_check.py",
    "backend/tests/smoke/test_rf2_closure_slides_runtime.py",
    "docs/codex/DOCX_PDF_REAL_INGESTION_RUNTIME.md",
    "backend/app/services/docx_service/ingestion.py",
    "backend/app/services/pdf_service/ingestion.py",
    "scripts/kw_docx_pdf_real_ingestion_check.py",
    "backend/tests/smoke/test_rf3_docx_pdf_real_ingestion.py",
    "backend/app/services/slides_service/runtime_closure.py",
    "scripts/kw_slides_runtime_closure_check.py",
    "backend/tests/smoke/test_rf2_7_slides_runtime_closure.py",
    "backend/app/services/slides_service/provenance_manifest_runtime.py",
    "scripts/kw_slides_provenance_manifest_runtime_check.py",
    "backend/tests/smoke/test_rf2_6_slides_provenance_manifest_runtime.py",
    "backend/app/services/slides_service/render_mode_runtime.py",
    "scripts/kw_slides_render_mode_runtime_check.py",
    "backend/tests/smoke/test_rf2_5_slides_render_mode_runtime.py",
    "backend/app/services/slides_service/approved_plan_lifecycle.py",
    "scripts/kw_slides_approved_plan_lifecycle_check.py",
    "backend/tests/smoke/test_rf2_3_slides_approved_plan_lifecycle.py",
    "docs/codex/K_PHASE_PRODUCT_POWER_PLAN.md",
    "docs/codex/K0_KIMI_LEVEL_RUBRIC_AND_GOLDEN_BENCHMARK.md",
    "backend/app/services/k_phase/kimi_level_rubric.py",
    "scripts/kw_k0_kimi_rubric_check.py",
    "backend/tests/smoke/test_k0_kimi_rubric.py",
    "docs/codex/K1_LOCAL_GIGACHAT_PLANNING_ENGINE.md",
    "backend/app/services/k_phase/local_gigachat_planner.py",
    "scripts/kw_k1_local_gigachat_planner_check.py",
    "backend/tests/smoke/test_k1_local_gigachat_planner.py",
    "docs/codex/K2_PLAN_EDITOR_PRODUCT_WORKFLOW.md",
    "backend/app/services/k_phase/plan_editor.py",
    "scripts/kw_k2_plan_editor_check.py",
    "backend/tests/smoke/test_k2_plan_editor_workflow.py",
    "docs/codex/K3_RENDERER_QUALITY_RUNTIME.md",
    "backend/app/services/k_phase/renderer_quality.py",
    "scripts/kw_k3_renderer_quality_check.py",
    "backend/tests/smoke/test_k3_renderer_quality_runtime.py",
    "docs/codex/K4_VISUAL_QA_RUNTIME.md",
    "backend/app/services/k_phase/visual_qa.py",
    "scripts/kw_k4_visual_qa_check.py",
    "backend/tests/smoke/test_k4_visual_qa_runtime.py",
    "docs/codex/RF_EXIT_TO_K_PHASE_CRITERIA.md",
    "scripts/kw_rf_to_k_transition_check.py",
    "backend/tests/smoke/test_rf2_2a_rf_to_k_transition.py",
    "backend/app/services/slides_service/approved_plan.py",
    "scripts/kw_slides_approved_plan_runtime_check.py",
    "backend/tests/smoke/test_rf2_2_slides_approved_plan_runtime.py",
    "scripts/kw_slides_runtime_inventory_check.py",
    "backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py",
    "docs/codex/CONTROLLED_DEPENDENCY_SECURITY_ASSESSMENT.md",
    "scripts/kw_controlled_dependency_security_assessment.py",
    "backend/tests/smoke/test_rf1_10_controlled_dependency_security_assessment.py",
    "scripts/kw_slides_runtime_phase_check.py",
    "backend/tests/smoke/test_rf2_0_slides_runtime_phase.py",
    "backend/tests/smoke/test_rf1_9_offline_operator_command_groups.py",
    "backend/tests/smoke/test_rf1_8_offline_build_readiness.py",
    "backend/tests/smoke/test_rf1_7_offline_artifact_inventory.py",
    "backend/tests/smoke/test_rf1_6_offline_bundle_integrity.py",
    "backend/tests/smoke/test_rf1_5_offline_bundle_artifact_presence.py",
    "scripts/kw_offline_bootstrap_bundle_tool.py",
    "backend/tests/smoke/test_rf1_4_offline_bootstrap_bundle_tooling.py",
    "scripts/kw_offline_bootstrap_manifest_check.py",
    "backend/tests/smoke/test_rf1_3_offline_bootstrap_manifest.py",
    "scripts/kw_offline_bootstrap_bundle_check.py",
    "backend/tests/smoke/test_rf1_2_offline_bootstrap_bundle.py", "backend/tests/smoke/test_rf1_offline_dependency_inventory.py", "backend/app/integrations/llm/litellm_gateway_contract.py",
    "scripts/kw_workflow_contracts_check.py", "scripts/kw_slides_plan_first_check.py",
    "scripts/kw_slides_task_events_check.py",
    "scripts/kw_slides_plan_editor_check.py",
    "scripts/kw_browser_evidence_capture_check.py",
    "scripts/kw_operator_smoke.py",
    "frontend/playwright.config.ts",
    "frontend/tests/e2e/deck-revision-smoke.spec.ts",
    "frontend/tests/e2e/version-timeline-smoke.spec.ts",
    "frontend/tests/e2e/version-restore-smoke.spec.ts",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
    ".env.deploy.example",
    "docs/deployment-packaging.md",
    "docs/schema-lifecycle.md",
    "docs/observability-baseline.md",
    "docs/offline-llm-topology.md",
    "docs/llm-provider-contract.md",
    "docs/litellm-gateway-topology.md",
    "docs/visual-qa-planning.md",
    "docs/heavy-node-runtime.md",
    "docs/workflow-contracts.md", "docs/slides-plan-first-ux.md",
    "docs/slides-task-events-and-retry.md",
    "docs/slides-plan-editor-ui.md",
    "docs/browser-evidence-capture.md",
    "docs/artifact-delivery-hardening.md",
    "docs/revision-restore.md",
    "docs/version-timeline-ui.md",
    "docs/codex/GIGACHAT_RUNTIME_HARDENING.md",
    "backend/app/integrations/llm/gigachat_runtime.py",
    "scripts/kw_gigachat_runtime_hardening_check.py",
    "backend/tests/smoke/test_rf4_gigachat_runtime_hardening.py",
    "docs/codex/RUNTIME_FOUNDATION_FINAL_CLOSURE.md",
    "backend/app/services/runtime_foundation_closure.py",
    "scripts/kw_runtime_foundation_closure_check.py",
    "backend/tests/smoke/test_rf_closure_runtime_foundation.py",
    "backend/tests/smoke/test_s9_litellm_gateway_contract.py",
)

SECRET_MARKERS = (
    "sk-proj-",
    "sk-live-",
    "xoxb-",
    "ghp_",
    "gho_",
    "ghu_",
    "github_pat_",
    "BEGIN PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY=",
    "OPENAI_API_KEY=sk-",
    "GIGACHAT_API_KEY=",
)

TEXT_SUFFIXES = {
    "",
    ".dockerignore",
    ".env",
    ".example",
    ".gitignore",
    ".ini",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

SECRET_MARKER_ALLOWLIST_FILES = {
    # These files intentionally contain marker literals as scanner catalogs or scanner tests.
    "scripts/kw_production_readiness_gate.py",
    "scripts/kw_validate_deployment_package.py",
    "backend/tests/smoke/test_p6_deployment_packaging.py",
    "backend/tests/smoke/test_p7_production_readiness_gate.py",
    "scripts/kw_dependency_audit.py",
    "backend/tests/smoke/test_r8_dependency_audit.py",
}


@dataclass(frozen=True)
class GateStep:
    name: str
    command: tuple[str, ...]
    cwd: Path | None = None


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(step: GateStep) -> None:
    cwd = step.cwd or Path.cwd()
    printable = " ".join(step.command)
    print()
    print("=" * 96)
    print(f"[STEP] {step.name}")
    print(f"$ {printable}")
    print("=" * 96)
    started = perf_counter()
    result = subprocess.run(step.command, cwd=cwd, text=True, check=False)
    elapsed = perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(f"[FAIL] {step.name} failed with exit code {result.returncode} after {elapsed:.1f}s")
    print(f"[PASS] {step.name} completed in {elapsed:.1f}s")


def require_files(repo_root: Path) -> list[str]:
    missing = [path for path in REQUIRED_P_PHASE_FILES if not (repo_root / path).exists()]
    return [f"missing expected P-phase file: {path}" for path in missing]


def is_text_candidate(path: Path) -> bool:
    if path.name in {"Makefile", "Dockerfile", "Dockerfile.backend"}:
        return True
    return path.suffix in TEXT_SUFFIXES or path.name.endswith(".env.deploy.example")


def iter_scannable_files(repo_root: Path) -> list[Path]:
    excluded_parts = {
        ".git",
        ".venv",
        "node_modules",
        ".next",
        ".pytest_cache",
        "__pycache__",
        "playwright-report",
        "test-results",
    }
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(part in excluded_parts for part in rel.parts):
            continue
        if is_text_candidate(path):
            files.append(path)
    return files


def scan_for_secret_markers(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in iter_scannable_files(repo_root):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(repo_root)
        rel_posix = rel.as_posix()
        if rel_posix in SECRET_MARKER_ALLOWLIST_FILES:
            continue
        for marker in SECRET_MARKERS:
            if marker in content:
                errors.append(f"potential secret marker '{marker}' found in {rel}")
    return errors


def checks_only(repo_root: Path) -> None:
    print(f"[INFO] repo_root={repo_root}")
    errors = []
    errors.extend(require_files(repo_root))
    errors.extend(scan_for_secret_markers(repo_root))
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        raise SystemExit(2)
    print("[PASS] required P-phase files are present")
    print("[PASS] no forbidden secret markers found in tracked text candidates")


def build_steps(repo_root: Path, args: argparse.Namespace) -> list[GateStep]:
    python = sys.executable
    frontend_dir = repo_root / "frontend"
    steps: list[GateStep] = []

    steps.append(GateStep("Git whitespace check", ("git", "diff", "--check"), repo_root))

    if args.require_clean_git:
        steps.append(GateStep("Git working tree is clean", ("git", "diff", "--exit-code"), repo_root))
        steps.append(GateStep("Git index is clean", ("git", "diff", "--cached", "--exit-code"), repo_root))

    steps.append(
        GateStep(
            "Deployment package validation",
            (python, "scripts/kw_validate_deployment_package.py", "--repo-root", str(repo_root)),
            repo_root,
        )
    )

    if not args.skip_preflight:
        steps.append(
            GateStep(
                "Deployment preflight static checks",
                (
                    python,
                    "scripts/kw_deployment_preflight.py",
                    "--repo-root",
                    str(repo_root),
                    "--skip-readiness",
                    "--skip-tests",
                    "--skip-frontend",
                ),
                repo_root,
            )
        )

    steps.append(
        GateStep(
            "Postgres schema lifecycle preflight",
            (python, "scripts/kw_schema_preflight.py", "--repo-root", str(repo_root), "--explain"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Runtime diagnostics",
            (python, "scripts/kw_runtime_diagnostics.py", "--repo-root", str(repo_root)),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline LLM topology contract",
            (python, "scripts/kw_llm_topology_check.py", "--repo-root", str(repo_root), "--allow-placeholders", "--require-ready"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "LiteLLM gateway optional transport contract",
            (
                python,
                "scripts/kw_litellm_gateway_check.py",
                "--repo-root",
                str(repo_root),
                "--allow-placeholders",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Workflow contracts registry",
            (python, "scripts/kw_workflow_contracts_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides plan-first UX contract",
            (python, "scripts/kw_slides_plan_first_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Slides task event retry contract",
            (python, "scripts/kw_slides_task_events_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Slides plan editor UI contract",
            (python, "scripts/kw_slides_plan_editor_check.py", "--repo-root", str(repo_root), "--require-ready"),
            repo_root,
        )
    )

    steps.append(

        GateStep(

            "Slides adaptive/template render mode contract",

            (python, "scripts/kw_slides_render_modes_check.py", "--repo-root", str(repo_root), "--require-ready"),

            repo_root,

        )

    )


    steps.append(
        GateStep(
            "Slides provenance manifest contract",
            (
                python,
                "scripts/kw_slides_provenance_manifest_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "generation",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Browser evidence capture contract",
            (
                python,
                "scripts/kw_browser_evidence_capture_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "capture",
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Browser evidence slides provenance link contract",
            (
                python,
                "scripts/kw_browser_evidence_capture_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "slides_link",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Visual QA planning contract",
            (
                python,
                "scripts/kw_visual_qa_planning_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "slides",
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Visual QA artifact planning contract",
            (
                python,
                "scripts/kw_visual_qa_planning_check.py",
                "--repo-root",
                str(repo_root),
                "--mode",
                "artifact",
                "--require-ready",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Offline dependency inventory contract",
            (
                python,
                "scripts/kw_offline_dependency_inventory_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bootstrap bundle strategy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bootstrap manifest validation contract",
            (
                python,
                "scripts/kw_offline_bootstrap_manifest_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bootstrap bundle tooling contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bundle artifact presence policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-artifact-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bundle checksum integrity policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-integrity-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline artifact inventory policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-inventory-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline bundle readiness report policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-readiness-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )
    steps.append(
        GateStep(
            "Offline operator command groups and RF1 closure policy contract",
            (
                python,
                "scripts/kw_offline_bootstrap_bundle_tool.py",
                "check-closure-policy",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides runtime phase checkpoint",
            (
                python,
                "scripts/kw_slides_runtime_phase_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Controlled dependency/security baseline assessment",
            (
                python,
                "scripts/kw_controlled_dependency_security_assessment.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides runtime capability inventory and baseline smoke",
            (
                python,
                "scripts/kw_slides_runtime_inventory_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides approved-plan deterministic PPTX runtime",
            (
                python,
                "scripts/kw_slides_approved_plan_runtime_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "K0 Kimi-level rubric and golden benchmark",
            (
                python,
                "scripts/kw_k0_kimi_rubric_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )



    steps.append(
        GateStep(
            "K2 Plan editor product workflow",
            (python, "scripts/kw_k2_plan_editor_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "K3 Renderer quality runtime",
            (python, "scripts/kw_k3_renderer_quality_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "K4 Visual QA runtime",
            (python, "scripts/kw_k4_visual_qa_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "K1 Local GigaChat planning engine",
            (python, "scripts/kw_k1_local_gigachat_planner_check.py", "--repo-root", str(repo_root), "--require-ready", "--json"),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "RF-to-K transition guard",
            (
                python,
                "scripts/kw_rf_to_k_transition_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "Slides approved-plan lifecycle runtime",
            (
                python,
                "scripts/kw_slides_approved_plan_lifecycle_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )


    steps.append(
        GateStep(
            "Slides saved-plan retry runtime",
            (
                python,
                "scripts/kw_slides_saved_plan_retry_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides provenance manifest runtime",
            (
                python,
                "scripts/kw_slides_provenance_manifest_runtime_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides render mode runtime hardening",
            (
                python,
                "scripts/kw_slides_render_mode_runtime_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides RF2 runtime closure and readiness",
            (
                python,
                "scripts/kw_slides_runtime_closure_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Slides RF2 final closure checkpoint",
            (
                python,
                "scripts/kw_slides_rf2_closure_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "DOCX/PDF real ingestion runtime",
            (
                python,
                "scripts/kw_docx_pdf_real_ingestion_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "GigaChat runtime hardening",
            (
                python,
                "scripts/kw_gigachat_runtime_hardening_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    steps.append(
        GateStep(
            "Runtime Foundation final closure checkpoint",
            (
                python,
                "scripts/kw_runtime_foundation_closure_check.py",
                "--repo-root",
                str(repo_root),
                "--require-ready",
                "--json",
            ),
            repo_root,
        )
    )

    if args.postgres_mode == "safety":
        steps.append(
            GateStep(
                "Postgres gate safety checks",
                (python, "scripts/kw_postgres_integration_gate.py", "--safety-only"),
                repo_root,
            )
        )
    elif args.postgres_mode == "optional":
        steps.append(GateStep("Optional real Postgres gate", (python, "scripts/kw_postgres_integration_gate.py"), repo_root))
    elif args.postgres_mode == "required":
        steps.append(
            GateStep(
                "Required real Postgres gate",
                (python, "scripts/kw_postgres_integration_gate.py", "--require-dsn"),
                repo_root,
            )
        )

    if not args.skip_backend:
        steps.append(GateStep("Backend full pytest suite", (python, "-m", "pytest", "-q"), repo_root))
        steps.append(GateStep("Backend compileall", (python, "-m", "compileall", "backend"), repo_root))

    if not args.skip_frontend:
        steps.append(GateStep("Frontend production build", ("npm", "run", "build"), frontend_dir))
        if not args.skip_e2e:
            steps.append(GateStep("Frontend E2E smoke", ("npm", "run", "test:e2e:smoke"), frontend_dir))

    return steps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the KW Studio P-phase production readiness final gate.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--checks-only", action="store_true", help="Only run static P-phase file and secret-marker checks.")
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend pytest and compileall.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build and E2E smoke.")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip frontend Playwright smoke.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip deployment preflight static checks.")
    parser.add_argument("--require-clean-git", action="store_true", help="Fail if tracked local changes are present.")
    parser.add_argument(
        "--postgres-mode",
        choices=("safety", "optional", "required"),
        default="safety",
        help="How to run the Postgres integration gate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}")
        return 2

    os.environ.setdefault("NEXT_TELEMETRY_DISABLED", "1")
    checks_only(repo_root)

    if args.checks_only:
        return 0

    steps = build_steps(repo_root, args)
    started = perf_counter()
    for step in steps:
        run_step(step)

    elapsed = perf_counter() - started
    print()
    print("=" * 96)
    print("[PRODUCTION READINESS GATE: PASS]")
    print(f"[INFO] completed {len(steps)} executable step(s) in {elapsed:.1f}s")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
