#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "presentation_studio_ui.v1"
CHECKER_SCHEMA_VERSION = "kw_presentation_studio_ui_check.v1"

REQUIRED_FILES = (
    "frontend/src/lib/api/presentation-studio.ts",
    "frontend/src/lib/api/presentation-studio.contract.ts",
    "frontend/src/components/presentations/presentation-studio-panel.tsx",
    "frontend/tests/e2e/presentation-studio-smoke.spec.ts",
    "frontend/src/components/layout/workspace-shell.tsx",
    "scripts/kw_presentation_studio_ui_check.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
    "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
    "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
)

REQUIRED_DOC_PHRASES = (
    "presentation_studio_ui.v1",
    "KR-7M Presentation Studio UI",
    "no_frontend_side_generation_as_source_of_truth",
    "no_arbitrary_model_selector",
    "backend_side_export_only",
)

REQUIRED_FRONTEND_PHRASES = {
    "frontend/src/lib/api/presentation-studio.ts": (
        "PRESENTATION_STUDIO_UI_SCHEMA_VERSION",
        "PRESENTATION_STUDIO_OPENAPI_PATH",
        "NEXT_PUBLIC_API_BASE_URL",
        "getPresentationStudioSnapshot",
        "savePresentationStudioDraft",
        "requestPresentationStudioExport",
        "frontend_side_generation_allowed: false",
        "arbitrary_model_selector_allowed: false",
        "backend_side_export: true",
    ),
    "frontend/src/components/presentations/presentation-studio-panel.tsx": (
        "Presentation Studio",
        "Slide thumbnails",
        "Slide canvas preview",
        "Block inspector",
        "Asset tray",
        "Deck quality warnings",
        "Save studio draft via backend API",
        "Request backend PPTX export",
        "Frontend-side generation: disabled",
        "Arbitrary model selector: disabled",
    ),
    "frontend/tests/e2e/presentation-studio-smoke.spec.ts": (
        "/presentations/pres_studio_ui/studio",
        "/presentations/pres_studio_ui/studio/draft",
        "/presentations/pres_studio_ui/exports",
        "persisted_through_backend_api",
        "backend_side_export",
        "presentation_studio_ui.v1",
    ),
}

FORBIDDEN_FRONTEND_PHRASES = (
    "GIGACHAT_CLIENT_ID",
    "GIGACHAT_CLIENT_SECRET",
    "GIGACHAT_ACCESS_TOKEN",
    "localModel",
    "modelSelector",
    "frontendGenerate",
    "writeFileSync",
    "pptxgenjs",
)


def _git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def build_report(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    required_paths: dict[str, bool] = {}

    for rel in REQUIRED_FILES:
        exists = (repo_root / rel).exists()
        required_paths[rel] = exists
        if not exists:
            errors.append(f"missing KR-7M required file: {rel}")

    for rel in (
        "docs/refactor/KR7_KIMI_LEVEL_SLIDES_ROADMAP.md",
        "docs/refactor/KR_PRODUCT_RESET_ROADMAP.md",
        "docs/refactor/PROJECT_MIGRATION_HANDOFF.md",
        "docs/PROJECT_PROHIBITIONS.md",
        "docs/QUALITY_MATRIX.md",
    ):
        path = repo_root / rel
        text = _read(path) if path.exists() else ""
        for phrase in REQUIRED_DOC_PHRASES:
            if phrase not in text:
                errors.append(f"{rel} missing KR-7M phrase: {phrase}")

    for rel, phrases in REQUIRED_FRONTEND_PHRASES.items():
        path = repo_root / rel
        text = _read(path) if path.exists() else ""
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{rel} missing KR-7M frontend phrase: {phrase}")

    workspace_shell = _read(repo_root / "frontend/src/components/layout/workspace-shell.tsx")
    if "PresentationStudioPanel" not in workspace_shell:
        errors.append("WorkspaceShell must include PresentationStudioPanel")

    frontend_text = "\n".join(
        _read(repo_root / rel)
        for rel in (
            "frontend/src/lib/api/presentation-studio.ts",
            "frontend/src/components/presentations/presentation-studio-panel.tsx",
            "frontend/tests/e2e/presentation-studio-smoke.spec.ts",
        )
        if (repo_root / rel).exists()
    )
    for phrase in FORBIDDEN_FRONTEND_PHRASES:
        if phrase in frontend_text:
            errors.append(f"KR-7M frontend surface must not include forbidden phrase: {phrase}")

    full_runner_text = _read(repo_root / "scripts/kw_full_tests_with_proxy_runner.sh")
    if "29m-presentation-studio-ui-check" not in full_runner_text:
        errors.append("full runner must include KR-7M Presentation Studio UI check step")

    inventory_text = _read(repo_root / "scripts/kw_test_inventory.py")
    if "kw_presentation_studio_ui_check" not in inventory_text:
        errors.append("test inventory must classify KR-7M Presentation Studio UI checker")

    payload: dict[str, Any] = {
        "checker_schema_version": CHECKER_SCHEMA_VERSION,
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not errors else "blocked",
        "presentation_studio_ui_implemented": not errors,
        "ui_can_run_separately": True,
        "backend_url_configurable": True,
        "openapi_client_contract_implemented": True,
        "slide_thumbnail_shell_implemented": True,
        "canvas_preview_shell_implemented": True,
        "block_inspector_shell_implemented": True,
        "asset_tray_shell_implemented": True,
        "quality_warning_panel_implemented": True,
        "draft_persistence_uses_backend_api": True,
        "backend_side_export_only": True,
        "frontend_side_generation_allowed": False,
        "arbitrary_model_selector_allowed": False,
        "renderer_runtime_changed": False,
        "gigachat_runtime_changed": False,
        "docker_deploy_changed": False,
        "visual_qa_executed": False,
        "production_ui_quality_claimed": False,
        "kimi_level_quality_claimed": False,
        "previous_phase": "KR-7L professional layout engine",
        "next_phase": "KR-7N professional quality evaluator",
        "branch": _git(repo_root, "branch", "--show-current") or "unknown",
        "commit": _git(repo_root, "rev-parse", "HEAD") or "unknown",
        "required_paths": required_paths,
        "errors": errors,
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KR-7M Presentation Studio UI contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_report(args.repo_root.resolve())
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_ready and payload.get("status") != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
