#!/usr/bin/env python3
"""KR-3B path portability cleanup plan/report.

KR-3B does not rewrite legacy files. It turns the KR-3A warn-only portability debt
into controlled cleanup batches so later patches can safely fix, reclassify, or
archive it.
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

from scripts.kw_path_portability_policy_check import (  # noqa: E402
    find_portability_markers,
    iter_text_files,
    legacy_scope_for,
    relpath,
    scan_legacy_summary,
)


REQUIRED_PLAN_FILES = (
    "scripts/kw_path_portability_cleanup_plan.py",
    "backend/tests/integrations/test_path_portability_cleanup_plan.py",
    "backend/tests/smoke/test_path_portability_cleanup_plan.py",
    "docs/refactor/PATH_PORTABILITY_CLEANUP_PLAN.md",
)

STAGE_PREFIXES = (
    "kw_s",
    "kw_p",
    "kw_rf",
    "kw_rch",
    "kw_rc",
    "kw_k",
    "kw_kq",
)

LOCAL_EXAMPLE_PATTERNS = {
    "absolute_home_path",
    "localized_downloads_path",
    "profile_specific_label",
}

BASELINE_PIN_PATTERNS = {
    "raw_git_sha",
    "release_branch_name",
}


@dataclass(frozen=True)
class CleanupItem:
    path: str
    line: int
    pattern: str
    scope: str
    batch: str
    action: str
    rationale: str
    snippet: str


@dataclass(frozen=True)
class CleanupBatch:
    key: str
    title: str
    action: str
    risk: str
    item_count: int
    done_when: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def collect_legacy_findings(repo_root: Path) -> list[dict[str, Any]]:
    repo_root = repo_root.resolve()
    findings: list[dict[str, Any]] = []
    for path in iter_text_files(repo_root):
        rel = relpath(path, repo_root)
        scope = legacy_scope_for(rel)
        if scope is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for finding in find_portability_markers(rel, text, scope):
            if finding.allowed:
                continue
            findings.append(asdict(finding))
    return findings


def classify_finding(finding: dict[str, Any]) -> CleanupItem:
    path = finding["path"]
    pattern = finding["pattern"]
    scope = finding["scope"]

    if path.startswith("docs/codex/"):
        batch = "docs_codex_dependency_retirement"
        action = "defer_until_stage_checker_dependencies_are_rewritten"
        rationale = (
            "Historical docs/codex references remain blocked by direct stage checker/test dependencies; "
            "do not move them until dependency inventory allows it."
        )
    elif path.startswith("scripts/kw_") and pattern in BASELINE_PIN_PATTERNS:
        name = path.rsplit("/", 1)[-1]
        if name.startswith(STAGE_PREFIXES):
            batch = "legacy_stage_baseline_pin_retirement"
            action = "archive_or_reclassify_stage_checker_after_product_replacement"
            rationale = (
                "Stage checker contains branch/commit baseline pins. Treat as legacy safety net, not active "
                "portable product behavior."
            )
        else:
            batch = "operator_script_portability_review"
            action = "replace hardcoded branch/commit assumptions with repo-root/options or archive script"
            rationale = "Operator script contains branch/commit assumptions and needs explicit product relevance review."
    elif pattern in LOCAL_EXAMPLE_PATTERNS:
        batch = "local_example_rewrite_or_mark"
        action = "rewrite as placeholders or mark as explicit local-only example"
        rationale = "Local path/profile/downloads examples must not look like required product runtime paths."
    elif scope == "legacy_or_smoke_test":
        batch = "legacy_test_replacement_or_archive"
        action = "replace with product-level tests or archive after replacement evidence"
        rationale = "Legacy smoke tests may encode stage assumptions; retire only after product coverage exists."
    elif scope == "kr_refactor_doc":
        batch = "refactor_doc_history_review"
        action = "keep as historical note or move to archive after active references are removed"
        rationale = "Refactor docs may contain historical paths/branches; keep separate from active product docs."
    else:
        batch = "manual_review"
        action = "review and classify before changing"
        rationale = "Finding does not fit an automatic cleanup category."

    return CleanupItem(
        path=path,
        line=int(finding["line"]),
        pattern=pattern,
        scope=scope,
        batch=batch,
        action=action,
        rationale=rationale,
        snippet=finding["snippet"],
    )


def batch_metadata(key: str, count: int) -> CleanupBatch:
    metadata: dict[str, tuple[str, str, str, str]] = {
        "legacy_stage_baseline_pin_retirement": (
            "Legacy stage baseline pin retirement",
            "archive_or_reclassify_stage_checkers_after_product_replacements",
            "medium",
            "stage scripts with raw SHAs/branch pins are either archived, removed from active gates, or rewritten without fixed branch/commit assumptions",
        ),
        "local_example_rewrite_or_mark": (
            "Local examples rewrite or mark",
            "rewrite_examples_as_placeholders_or_add_local_only_context",
            "low",
            "no unmarked /home, profile, Downloads, or localized Downloads examples remain in active docs/tests/scripts",
        ),
        "docs_codex_dependency_retirement": (
            "docs/codex dependency retirement",
            "defer_until_stage_checker_dependency_inventory_is_cleared",
            "high",
            "direct docs/codex dependencies are removed from active checkers/tests before physical archive",
        ),
        "legacy_test_replacement_or_archive": (
            "Legacy smoke test replacement/archive",
            "replace_stage_tests_with_product_tests_or_archive_later",
            "medium",
            "legacy tests are no longer needed by full runner or have product-level replacements",
        ),
        "operator_script_portability_review": (
            "Operator script portability review",
            "rewrite_operator_scripts_to_use_arguments_or_archive",
            "medium",
            "operator scripts do not require fixed branch, commit, machine, or profile assumptions",
        ),
        "refactor_doc_history_review": (
            "Refactor/history docs review",
            "move_historical_notes_out_of_active_docs_or_keep_as_history",
            "low",
            "historical references are clearly separated from active product/operator instructions",
        ),
        "manual_review": (
            "Manual review",
            "classify_before_changing",
            "unknown",
            "all remaining findings have an explicit owner category",
        ),
    }
    title, action, risk, done_when = metadata.get(key, metadata["manual_review"])
    return CleanupBatch(key=key, title=title, action=action, risk=risk, item_count=count, done_when=done_when)


def build_cleanup_plan(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    raw_findings = collect_legacy_findings(repo_root)
    items = [classify_finding(finding) for finding in raw_findings]

    counts_by_batch: dict[str, int] = {}
    counts_by_pattern: dict[str, int] = {}
    counts_by_scope: dict[str, int] = {}
    for item in items:
        counts_by_batch[item.batch] = counts_by_batch.get(item.batch, 0) + 1
        counts_by_pattern[item.pattern] = counts_by_pattern.get(item.pattern, 0) + 1
        counts_by_scope[item.scope] = counts_by_scope.get(item.scope, 0) + 1

    batches = [batch_metadata(key, count) for key, count in sorted(counts_by_batch.items())]

    missing_plan_files = [path for path in REQUIRED_PLAN_FILES if not (repo_root / path).exists()]
    issues: list[str] = []
    for path in missing_plan_files:
        issues.append(f"required KR-3B plan file missing: {path}")

    legacy_summary = scan_legacy_summary(repo_root)

    return {
        "generated_at": utc_now(),
        "status": "ready" if not issues else "blocked",
        "purpose": "KR-3B path portability cleanup plan/report; legacy findings are planned, not fixed in this patch.",
        "summary": {
            "legacy_findings_total": len(items),
            "cleanup_batch_count": len(batches),
            "required_plan_files": len(REQUIRED_PLAN_FILES),
            "required_plan_files_missing": len(missing_plan_files),
            "physical_docs_codex_archive_allowed": False,
            "docs_codex_archive_blocked_until": "direct docs/codex dependencies are rewritten or archived",
            "legacy_warn_only_total_from_policy_scanner": legacy_summary["warn_only_total"],
        },
        "counts_by_batch": dict(sorted(counts_by_batch.items())),
        "counts_by_pattern": dict(sorted(counts_by_pattern.items())),
        "counts_by_scope": dict(sorted(counts_by_scope.items())),
        "cleanup_batches": [asdict(batch) for batch in batches],
        "cleanup_items": [asdict(item) for item in items],
        "issues": issues,
        "next_steps": [
            "KR-3C: retire or reclassify legacy stage baseline pins that are no longer active product gates.",
            "KR-3D: rewrite unmarked local examples as placeholders or explicitly mark local-only examples.",
            "KR-3E: revisit docs/codex movement only after stage dependency inventory no longer blocks physical archive.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# KR-3B Path Portability Cleanup Plan",
        "",
        "KR-3B turns KR-3A warn-only portability debt into controlled cleanup batches.",
        "It does not rewrite or archive legacy files yet.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Legacy findings total: `{summary['legacy_findings_total']}`",
        f"- Cleanup batches: `{summary['cleanup_batch_count']}`",
        f"- Required plan files missing: `{summary['required_plan_files_missing']}`",
        f"- Physical `docs/codex` archive allowed: `{summary['physical_docs_codex_archive_allowed']}`",
        f"- Blocked until: `{summary['docs_codex_archive_blocked_until']}`",
        "",
        "## Cleanup batches",
        "",
    ]
    for batch in report["cleanup_batches"]:
        lines.extend(
            [
                f"### {batch['title']}",
                "",
                f"- Key: `{batch['key']}`",
                f"- Action: `{batch['action']}`",
                f"- Risk: `{batch['risk']}`",
                f"- Item count: `{batch['item_count']}`",
                f"- Done when: {batch['done_when']}",
                "",
            ]
        )

    lines.extend(["## Counts by pattern", ""])
    for key, count in report["counts_by_pattern"].items():
        lines.append(f"- `{key}`: {count}")

    lines.extend(["", "## Top cleanup items", ""])
    for item in report["cleanup_items"][:50]:
        lines.append(
            f"- `{item['path']}:{item['line']}` — `{item['pattern']}` → `{item['batch']}`"
        )
    if len(report["cleanup_items"]) > 50:
        lines.append(f"- ... plus {len(report['cleanup_items']) - 50} more items.")

    lines.extend(["", "## Issues", ""])
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
    parser = argparse.ArgumentParser(description="Build KR-3B path portability cleanup plan.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip-out", type=Path, default=None)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_cleanup_plan(args.repo_root)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "kr3b_path_portability_cleanup_plan.json", report)
    (output_dir / "kr3b_path_portability_cleanup_plan.md").write_text(render_markdown(report), encoding="utf-8")

    if args.zip_out:
        write_zip(output_dir, args.zip_out.resolve())

    if args.json:
        print(json.dumps({"status": report["status"], **report["summary"], "counts_by_batch": report["counts_by_batch"]}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KR-3B path portability cleanup plan: {report['status']}")
        print(f"Report written to: {output_dir}")

    if args.require_ready and report["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
