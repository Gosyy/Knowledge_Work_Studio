#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.slides_service.template_master_ingestion import (  # noqa: E402
    template_master_ingestion_report,
    validate_local_template_reference,
)

CHECKPOINT = "S5"
EXPECTED_BASE_AFTER_S4 = "f04190dc56d7817401482f04b1289aa6bb2d0a6e"
REQUIRED_FILES = (
    "docs/codex/S_PHASE_KIMI_SLIDES_CLASS_ROADMAP.md",
    "docs/codex/S3_ADAPTIVE_DECK_MODES.md",
    "docs/codex/S4_NATIVE_TABLE_CHART_DIAGRAM_RENDERING.md",
    "docs/codex/S5_TEMPLATE_MASTER_INGESTION.md",
    "backend/app/services/slides_service/adaptive_deck_modes.py",
    "backend/app/services/slides_service/native_visuals.py",
    "backend/app/services/slides_service/template_master_ingestion.py",
    "scripts/kw_s4_native_visual_rendering_check.py",
    "scripts/kw_s5_template_master_ingestion_check.py",
    "backend/tests/smoke/test_s5_template_master_ingestion.py",
)


def run_git(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(("git", *args), cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool | None:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def run_checker(repo_root: Path, script: str, require_ready: bool) -> tuple[dict[str, Any] | None, int, str]:
    command = [sys.executable, script, "--repo-root", str(repo_root), "--json"]
    if require_ready:
        command.append("--require-ready")
    result = subprocess.run(command, cwd=repo_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    payload: dict[str, Any] | None = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return payload, result.returncode, result.stderr.strip() or result.stdout.strip()[:500]


def collect_static_errors(repo_root: Path, require_ready: bool) -> list[str]:
    errors = [f"missing S5 required file: {rel}" for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
    if require_ready:
        branch = run_git(repo_root, "branch", "--show-current")
        if branch not in ("9_Product_Release_Hardening", "8_K_Phase"):
            errors.append(f"expected branch 9_Product_Release_Hardening or 8_K_Phase, got {branch}")
        head = run_git(repo_root, "rev-parse", "HEAD")
        if head and head != EXPECTED_BASE_AFTER_S4:
            ancestry = is_ancestor(repo_root, EXPECTED_BASE_AFTER_S4, head)
            if ancestry is False:
                errors.append(f"expected S4 baseline {EXPECTED_BASE_AFTER_S4} to be an ancestor of HEAD {head}")
            elif ancestry is None:
                errors.append(f"could not verify S4 ancestry for {EXPECTED_BASE_AFTER_S4}..{head}")
        s4_report, returncode, details = run_checker(repo_root, "scripts/kw_s4_native_visual_rendering_check.py", True)
        if returncode != 0 or not isinstance(s4_report, dict) or s4_report.get("status") != "ready":
            errors.append(f"S5 requires ready S4 native visual rendering evidence: {details}")
    return errors


def build_report(repo_root: Path, require_ready: bool) -> dict[str, Any]:
    errors = collect_static_errors(repo_root, require_ready)
    report = template_master_ingestion_report()
    if errors:
        report = dict(report)
        report["errors"] = list(report.get("errors", [])) + errors
        report["status"] = "not_ready"
        report["template_master_ingestion_completed_by_s5"] = False
    report["checkpoint"] = CHECKPOINT
    report["branch"] = run_git(repo_root, "branch", "--show-current") or "unknown"
    report["commit"] = run_git(repo_root, "rev-parse", "HEAD") or "unknown"
    report["expected_base_after_s4"] = EXPECTED_BASE_AFTER_S4
    report["required_paths"] = {rel: (repo_root / rel).exists() for rel in REQUIRED_FILES}
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate KW Studio S5 template and slide-master ingestion contract.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--validate-template-ref", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    if args.validate_template_ref is not None:
        errors = validate_local_template_reference(args.validate_template_ref)
        payload = {"status": "ready" if not errors else "not_ready", "template_reference": args.validate_template_ref, "errors": errors}
    else:
        payload = build_report(repo_root, args.require_ready)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))
        if payload.get("status") == "ready":
            print("[PASS] S5 template and slide-master ingestion contract completed")
        else:
            for error in payload.get("errors", []):
                print(f"[FAIL] {error}")
    if args.require_ready and payload.get("status") != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
