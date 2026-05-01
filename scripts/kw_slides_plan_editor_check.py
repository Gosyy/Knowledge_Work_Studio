#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = (
    "frontend/src/components/presentations/slides-plan-editor-panel.tsx",
    "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts",
    "docs/slides-plan-editor-ui.md",
)

REQUIRED_COMPONENT_MARKERS = (
    "Slides plan editor",
    "Plan editor presentation id",
    "Editable saved plan",
    "Editable deck title",
    "Adaptive mode",
    "Template mode",
    "Save editable plan draft",
    "Prepare retry from saved plan",
    "Retry from saved plan ready",
    "slides.retry.from_saved_plan.requested",
)

REQUIRED_DOC_MARKERS = (
    "S5",
    "editable plan",
    "retry from saved plan",
    "adaptive",
    "template",
    "offline",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def validate(repo_root: Path) -> dict[str, object]:
    errors: list[str] = []
    files: dict[str, bool] = {}
    for relative in REQUIRED_FILES:
        exists = (repo_root / relative).is_file()
        files[relative] = exists
        if not exists:
            errors.append(f"missing required S5 file: {relative}")

    component_path = repo_root / "frontend/src/components/presentations/slides-plan-editor-panel.tsx"
    component_text = component_path.read_text(encoding="utf-8") if component_path.is_file() else ""
    for marker in REQUIRED_COMPONENT_MARKERS:
        if marker not in component_text:
            errors.append(f"missing S5 component marker: {marker}")

    workspace_path = repo_root / "frontend/src/components/layout/workspace-shell.tsx"
    workspace_text = workspace_path.read_text(encoding="utf-8") if workspace_path.is_file() else ""
    if "SlidesPlanEditorPanel" not in workspace_text:
        errors.append("workspace shell must render SlidesPlanEditorPanel")

    e2e_path = repo_root / "frontend/tests/e2e/slides-plan-editor-smoke.spec.ts"
    e2e_text = e2e_path.read_text(encoding="utf-8") if e2e_path.is_file() else ""
    for marker in ("Load editable plan", "Save editable plan draft", "Prepare retry from saved plan"):
        if marker not in e2e_text:
            errors.append(f"missing S5 E2E marker: {marker}")

    doc_path = repo_root / "docs/slides-plan-editor-ui.md"
    doc_text = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
    lowered_doc = doc_text.lower()
    for marker in REQUIRED_DOC_MARKERS:
        if marker.lower() not in lowered_doc:
            errors.append(f"missing S5 documentation marker: {marker}")

    return {
        "status": "ready" if not errors else "not_ready",
        "files": files,
        "component_marker_count": len(REQUIRED_COMPONENT_MARKERS),
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the S5 slides plan editor UI contract.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--require-ready", action="store_true", help="Fail unless the S5 UI contract is ready.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = validate(repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[slides-plan-editor-ui]")
        print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "ready":
        print("[FAIL] S5 slides plan editor UI contract is not ready")
        return 2
    print("[PASS] S5 slides plan editor UI contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
