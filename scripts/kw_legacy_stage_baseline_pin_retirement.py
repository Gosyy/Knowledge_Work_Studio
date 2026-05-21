#!/usr/bin/env python3
"""KR-3C legacy stage baseline pin retirement batch 1.

KR-3C executes the first controlled retirement step for legacy stage baseline
pins by creating a machine-readable batch manifest. It does not edit the legacy
stage scripts in-place and does not remove docs/codex.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.kw_path_portability_cleanup_plan import build_cleanup_plan  # noqa: E402


REQUIRED_RETIREMENT_FILES = (
    "scripts/kw_legacy_stage_baseline_pin_retirement.py",
    "backend/tests/integrations/test_legacy_stage_baseline_pin_retirement.py",
    "backend/tests/smoke/test_legacy_stage_baseline_pin_retirement.py",
    "docs/refactor/LEGACY_STAGE_BASELINE_PIN_RETIREMENT_BATCH1.md",
)

ACTIVE_REFERENCE_FILES = (
    "scripts/kw_production_readiness_gate.py",
    "scripts/kw_full_tests_with_proxy_runner.sh",
    "scripts/kw_path_portability_policy_check.py",
    "scripts/kw_path_portability_cleanup_plan.py",
)

BATCH_KEY = "legacy_stage_baseline_pin_retirement"
DEFAULT_BATCH1_MAX_PATHS = 12


@dataclass(frozen=True)
class StagePinGroup:
    path: str
    item_count: int
    patterns: tuple[str, ...]
    active_reference_count: int
    active_reference_files: tuple[str, ...]
    batch1_action: str
    rationale: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def active_reference_files_for(repo_root: Path, rel_path: str) -> tuple[str, ...]:
    basename = rel_path.rsplit("/", 1)[-1]
    references: list[str] = []
    for active_rel in ACTIVE_REFERENCE_FILES:
        active_path = repo_root / active_rel
        text = read_text_if_exists(active_path)
        if rel_path in text or basename in text:
            references.append(active_rel)
    return tuple(references)


def build_stage_pin_groups(repo_root: Path) -> list[StagePinGroup]:
    plan = build_cleanup_plan(repo_root)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in plan["cleanup_items"]:
        if item["batch"] != BATCH_KEY:
            continue
        grouped.setdefault(item["path"], []).append(item)

    groups: list[StagePinGroup] = []
    for path, items in grouped.items():
        patterns = tuple(sorted({item["pattern"] for item in items}))
        active_refs = active_reference_files_for(repo_root, path)
        if active_refs:
            action = "reclassify_as_legacy_safety_net_before_editing"
            rationale = (
                "This stage checker is still referenced by an active runner/gate. "
                "KR-3C batch 1 records it in the retirement manifest but does not edit or remove it."
            )
        else:
            action = "eligible_for_archive_after_product_replacement_verification"
            rationale = (
                "This stage checker is not referenced by the active runner/gate set inspected by KR-3C. "
                "It can be archived later after product replacement evidence is accepted."
            )

        groups.append(
            StagePinGroup(
                path=path,
                item_count=len(items),
                patterns=patterns,
                active_reference_count=len(active_refs),
                active_reference_files=active_refs,
                batch1_action=action,
                rationale=rationale,
            )
        )
    return sorted(groups, key=lambda group: (-group.item_count, group.path))


def select_batch1(groups: list[StagePinGroup], max_paths: int = DEFAULT_BATCH1_MAX_PATHS) -> list[StagePinGroup]:
    inactive = [group for group in groups if group.active_reference_count == 0]
    active = [group for group in groups if group.active_reference_count > 0]
    selected = inactive[:max_paths]
    if len(selected) < max_paths:
        selected.extend(active[: max_paths - len(selected)])
    return selected


def build_retirement_report(repo_root: Path, *, max_paths: int = DEFAULT_BATCH1_MAX_PATHS) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cleanup_plan = build_cleanup_plan(repo_root)
    all_groups = build_stage_pin_groups(repo_root)
    batch1_groups = select_batch1(all_groups, max_paths=max_paths)
    missing_files = [path for path in REQUIRED_RETIREMENT_FILES if not (repo_root / path).exists()]

    issues: list[str] = []
    for path in missing_files:
        issues.append(f"required KR-3C retirement file missing: {path}")
    if cleanup_plan["counts_by_batch"].get(BATCH_KEY, 0) <= 0:
        issues.append("cleanup plan has no legacy stage baseline pin items to retire")
    if not batch1_groups:
        issues.append("KR-3C batch 1 selected no stage baseline pin groups")

    batch1_item_count = sum(group.item_count for group in batch1_groups)
    active_referenced_batch1_count = sum(1 for group in batch1_groups if group.active_reference_count > 0)
    inactive_batch1_count = len(batch1_groups) - active_referenced_batch1_count

    return {
        "generated_at": utc_now(),
        "status": "ready" if not issues else "blocked",
        "purpose": (
            "KR-3C batch 1 retires legacy stage baseline pins by manifest/reclassification. "
            "It does not edit active stage scripts, remove tests, or move docs/codex."
        ),
        "summary": {
            "legacy_stage_baseline_pin_items_total": cleanup_plan["counts_by_batch"].get(BATCH_KEY, 0),
            "legacy_stage_baseline_pin_paths_total": len(all_groups),
            "batch1_paths_selected": len(batch1_groups),
            "batch1_items_selected": batch1_item_count,
            "batch1_inactive_paths_selected": inactive_batch1_count,
            "batch1_active_referenced_paths_selected": active_referenced_batch1_count,
            "execution_mode": "retirement_manifest_and_reclassification",
            "physical_docs_codex_archive_allowed": False,
            "required_retirement_files": len(REQUIRED_RETIREMENT_FILES),
            "required_retirement_files_missing": len(missing_files),
        },
        "batch1_groups": [asdict(group) for group in batch1_groups],
        "all_stage_pin_groups": [asdict(group) for group in all_groups],
        "issues": issues,
        "next_steps": [
            "KR-3D: rewrite or mark local examples after batch 1 manifest is accepted.",
            "KR-3E: remove active gate references before editing or archiving referenced stage checkers.",
            "Later cleanup: archive inactive batch 1 stage checkers only after full runner proves product replacements.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KR-3C Legacy Stage Baseline Pin Retirement Batch 1",
        "",
        "KR-3C executes the first controlled retirement batch for legacy stage baseline pins.",
        "This patch creates a manifest and reclassification report; it does not edit active legacy scripts in-place.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Total baseline-pin items: `{summary['legacy_stage_baseline_pin_items_total']}`",
        f"- Total baseline-pin paths: `{summary['legacy_stage_baseline_pin_paths_total']}`",
        f"- Batch 1 paths selected: `{summary['batch1_paths_selected']}`",
        f"- Batch 1 items selected: `{summary['batch1_items_selected']}`",
        f"- Inactive selected paths: `{summary['batch1_inactive_paths_selected']}`",
        f"- Active-referenced selected paths: `{summary['batch1_active_referenced_paths_selected']}`",
        f"- Execution mode: `{summary['execution_mode']}`",
        f"- Physical `docs/codex` archive allowed: `{summary['physical_docs_codex_archive_allowed']}`",
        "",
        "## Batch 1 groups",
        "",
    ]
    for group in report["batch1_groups"]:
        refs = ", ".join(group["active_reference_files"]) or "none"
        lines.extend(
            [
                f"### `{group['path']}`",
                "",
                f"- Item count: `{group['item_count']}`",
                f"- Patterns: `{', '.join(group['patterns'])}`",
                f"- Active references: `{refs}`",
                f"- Action: `{group['batch1_action']}`",
                f"- Rationale: {group['rationale']}",
                "",
            ]
        )

    lines.extend(["## Issues", ""])
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- None")

    lines.extend(["", "## Next steps", ""])
    for step in report["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build KR-3C legacy stage baseline pin retirement batch 1 report.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--max-paths", type=int, default=DEFAULT_BATCH1_MAX_PATHS)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_retirement_report(args.repo_root, max_paths=args.max_paths)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "kr3c_legacy_stage_baseline_pin_retirement.json", report)
    (output_dir / "kr3c_legacy_stage_baseline_pin_retirement.md").write_text(render_markdown(report), encoding="utf-8")

    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-3C legacy stage baseline pin retirement: {report['status']}")
        print(f"Report written to: {output_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
