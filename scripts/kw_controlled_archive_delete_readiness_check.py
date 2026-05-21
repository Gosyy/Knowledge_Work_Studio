#!/usr/bin/env python3
"""Validate KR-3F controlled archive/delete readiness batch 1.

The checker proves that the first physical cleanup batch only moved inactive
root-level historical prompt packs into the development-history archive and did
not move docs/codex or remove legacy safety-net files blindly.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

ARCHIVE_ROOT = Path("docs/archive/development-history/root-prompt-packs")

BATCH1_ARCHIVE_MOVES: tuple[tuple[str, str], ...] = (
    (
        "F_L_ANTI_SCOPE_PROMPTS_REVISED.md",
        "docs/archive/development-history/root-prompt-packs/F_L_ANTI_SCOPE_PROMPTS_REVISED.md",
    ),
    (
        "M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md",
        "docs/archive/development-history/root-prompt-packs/M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md",
    ),
    (
        "N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
        "docs/archive/development-history/root-prompt-packs/N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
    ),
    (
        "O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
        "docs/archive/development-history/root-prompt-packs/O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
    ),
    ("PROMPTS_1_5.md", "docs/archive/development-history/root-prompt-packs/PROMPTS_1_5.md"),
    (
        "R_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
        "docs/archive/development-history/root-prompt-packs/R_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md",
    ),
    ("R_PHASE_ISSUE_PACK.md", "docs/archive/development-history/root-prompt-packs/R_PHASE_ISSUE_PACK.md"),
)

REQUIRED_POLICY_DOCS: tuple[str, ...] = (
    "docs/refactor/CONTROLLED_ARCHIVE_DELETE_READINESS.md",
    "docs/archive/development-history/root-prompt-packs/README.md",
)

ALLOWED_OLD_PATH_REFERENCE_FILES: tuple[str, ...] = (
    "docs/refactor/CONTROLLED_ARCHIVE_DELETE_READINESS.md",
    "docs/archive/development-history/root-prompt-packs/README.md",
    "scripts/kw_controlled_archive_delete_readiness_check.py",
    "backend/tests/integrations/test_controlled_archive_delete_readiness.py",
    "backend/tests/smoke/test_controlled_archive_delete_readiness.py",
)

EXCLUDED_SCAN_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "playwright-report",
    "test-results",
    "logs",
}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


def _is_scannable(path: Path) -> bool:
    if path.name in {"Dockerfile", "Dockerfile.backend", "Makefile"}:
        return True
    return path.suffix in TEXT_SUFFIXES or path.name.endswith(".env.deploy.example")


def iter_active_text_files(repo_root: Path) -> Iterable[Path]:
    archive_root = repo_root / ARCHIVE_ROOT
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root)
        if any(part in EXCLUDED_SCAN_PARTS for part in rel.parts):
            continue
        if archive_root in path.parents:
            continue
        if rel.as_posix() in ALLOWED_OLD_PATH_REFERENCE_FILES:
            continue
        if _is_scannable(path):
            yield path


def find_active_old_path_references(repo_root: Path, old_paths: Iterable[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    old_path_list = list(old_paths)
    for path in iter_active_text_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(repo_root).as_posix()
        for old_path in old_path_list:
            old_name = Path(old_path).name
            if old_path in text or old_name in text:
                findings.append({"file": rel, "old_path": old_path})
    return findings


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    old_paths = [old for old, _new in BATCH1_ARCHIVE_MOVES]
    new_paths = [new for _old, new in BATCH1_ARCHIVE_MOVES]

    root_paths_still_present = [old for old in old_paths if (repo_root / old).exists()]
    missing_archive_paths = [new for new in new_paths if not (repo_root / new).exists()]
    missing_policy_docs = [rel for rel in REQUIRED_POLICY_DOCS if not (repo_root / rel).exists()]
    active_old_path_references = find_active_old_path_references(repo_root, old_paths)

    docs_codex_dir = repo_root / "docs" / "codex"
    docs_codex_files = sorted(p.relative_to(repo_root).as_posix() for p in docs_codex_dir.glob("*.md")) if docs_codex_dir.exists() else []
    docs_codex_paths_in_batch = [new for new in new_paths if new.startswith("docs/codex/")] + [
        old for old in old_paths if old.startswith("docs/codex/")
    ]

    production_gate = repo_root / "scripts" / "kw_production_readiness_gate.py"
    gate_text = production_gate.read_text(encoding="utf-8") if production_gate.exists() else ""
    gate_references_checker = "scripts/kw_controlled_archive_delete_readiness_check.py" in gate_text

    issues: list[str] = []
    for old in root_paths_still_present:
        issues.append(f"old root archive candidate still present: {old}")
    for new in missing_archive_paths:
        issues.append(f"missing archived path: {new}")
    for rel in missing_policy_docs:
        issues.append(f"missing KR-3F policy/archive document: {rel}")
    for finding in active_old_path_references:
        issues.append(f"active reference to old root path {finding['old_path']} in {finding['file']}")
    if docs_codex_paths_in_batch:
        issues.append("KR-3F batch 1 must not include docs/codex paths")
    if not docs_codex_files:
        issues.append("docs/codex unexpectedly missing; physical docs/codex archive remains blocked")
    if not gate_references_checker:
        issues.append("production readiness gate must run KR-3F archive/delete readiness checker")

    return {
        "status": "ready" if not issues else "not_ready",
        "batch": "KR-3F controlled archive/delete readiness batch 1",
        "archive_root": ARCHIVE_ROOT.as_posix(),
        "moved_paths_count": len(BATCH1_ARCHIVE_MOVES),
        "moved_paths": [{"old": old, "new": new} for old, new in BATCH1_ARCHIVE_MOVES],
        "root_paths_still_present": root_paths_still_present,
        "missing_archive_paths": missing_archive_paths,
        "missing_policy_docs": missing_policy_docs,
        "active_old_path_references": active_old_path_references,
        "active_old_path_references_count": len(active_old_path_references),
        "docs_codex_files_still_present_count": len(docs_codex_files),
        "docs_codex_paths_in_batch": docs_codex_paths_in_batch,
        "production_gate_references_checker": gate_references_checker,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless report is ready.")
    args = parser.parse_args()

    report = build_report(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"KR-3F controlled archive/delete readiness status: {report['status']}")
        if report["issues"]:
            print("Issues:")
            for issue in report["issues"]:
                print(f"- {issue}")
    if args.require_ready and report["status"] != "ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
