#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARCHIVE_ROOT = Path("docs/archive/development-history")


@dataclass(frozen=True)
class ArchiveDecision:
    source: str
    destination: str
    priority: str
    reason: str


@dataclass(frozen=True)
class ArchiveResult:
    source: str
    destination: str
    status: str
    reason: str


def load_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"cleanup policy not found: {path}")
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as archive:
            try:
                with archive.open("cleanup_policy.json") as handle:
                    return json.loads(handle.read().decode("utf-8"))
            except KeyError as exc:
                raise ValueError(f"policy ZIP does not contain cleanup_policy.json: {path}") from exc
    return json.loads(path.read_text(encoding="utf-8"))


def archive_destination_for(source: str) -> str:
    if not source.startswith("docs/"):
        raise ValueError(f"only docs/ paths can be archived by KR-1B: {source}")
    relative_under_docs = source[len("docs/") :]
    return (ARCHIVE_ROOT / relative_under_docs).as_posix()


def archive_decisions(policy: dict[str, Any]) -> list[ArchiveDecision]:
    decisions: list[ArchiveDecision] = []
    for item in policy.get("decisions", []):
        if item.get("kind") != "doc" or item.get("action") != "archive":
            continue
        source = str(item.get("path", ""))
        if not source.startswith("docs/") or source.startswith("docs/archive/"):
            continue
        decisions.append(
            ArchiveDecision(
                source=source,
                destination=archive_destination_for(source),
                priority=str(item.get("priority", "medium")),
                reason=str(item.get("reason", "obsolete stage documentation")),
            )
        )
    return sorted(decisions, key=lambda decision: decision.source)


def _safe_relative_path(path: str) -> None:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe repository-relative path: {path}")


def _move_file(repo_root: Path, decision: ArchiveDecision, *, execute: bool, allow_missing: bool) -> ArchiveResult:
    _safe_relative_path(decision.source)
    _safe_relative_path(decision.destination)
    source_path = repo_root / decision.source
    destination_path = repo_root / decision.destination

    if destination_path.exists() and not source_path.exists():
        return ArchiveResult(decision.source, decision.destination, "already_archived", decision.reason)

    if not source_path.exists():
        status = "missing_allowed" if allow_missing else "missing"
        return ArchiveResult(decision.source, decision.destination, status, decision.reason)

    if source_path.is_dir():
        return ArchiveResult(decision.source, decision.destination, "skipped_directory", decision.reason)

    if not execute:
        return ArchiveResult(decision.source, decision.destination, "planned", decision.reason)

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.exists():
        return ArchiveResult(decision.source, decision.destination, "destination_exists", decision.reason)
    shutil.move(str(source_path), str(destination_path))
    return ArchiveResult(decision.source, decision.destination, "moved", decision.reason)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _markdown_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> str:
    if not rows:
        return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n"
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        escaped = [cell.replace("|", "\\|").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines) + "\n"


def write_manifest(output_dir: Path, payload: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "obsolete_stage_docs_archive_manifest.json", payload)

    result_rows = [
        (
            item["status"],
            item["source"],
            item["destination"],
            item["reason"],
        )
        for item in payload["results"][:150]
    ]
    markdown = "\n".join(
        [
            "# Obsolete stage documentation archive manifest",
            "",
            "KR-1B moves stage-specific development documentation out of active docs.",
            "",
            "## Summary",
            "",
            _markdown_table(
                [(key, str(value)) for key, value in payload["summary"].items()],
                ("Metric", "Value"),
            ),
            "## Results",
            "",
            _markdown_table(result_rows, ("Status", "Source", "Destination", "Reason")),
        ]
    )
    (output_dir / "obsolete_stage_docs_archive_manifest.md").write_text(markdown + "\n", encoding="utf-8")


def build_report(
    *,
    repo_root: Path,
    policy_path: Path,
    decisions: list[ArchiveDecision],
    results: list[ArchiveResult],
    execute: bool,
) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for result in results:
        statuses[result.status] = statuses.get(result.status, 0) + 1
    blocking_statuses = {"missing", "destination_exists", "skipped_directory"}
    blocking = [result for result in results if result.status in blocking_statuses]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "policy_path": str(policy_path),
        "mode": "execute" if execute else "dry_run",
        "archive_root": ARCHIVE_ROOT.as_posix(),
        "status": "ready" if not blocking else "blocked",
        "summary": {
            "decision_count": len(decisions),
            "planned_count": statuses.get("planned", 0),
            "moved_count": statuses.get("moved", 0),
            "already_archived_count": statuses.get("already_archived", 0),
            "missing_allowed_count": statuses.get("missing_allowed", 0),
            "missing_count": statuses.get("missing", 0),
            "destination_exists_count": statuses.get("destination_exists", 0),
            "blocking_issue_count": len(blocking),
        },
        "decisions": [asdict(decision) for decision in decisions],
        "results": [asdict(result) for result in results],
    }


def archive_obsolete_stage_docs(
    *,
    repo_root: Path,
    policy_path: Path,
    output_dir: Path,
    execute: bool,
    allow_missing: bool,
) -> dict[str, Any]:
    policy = load_policy(policy_path)
    decisions = archive_decisions(policy)
    results = [
        _move_file(repo_root, decision, execute=execute, allow_missing=allow_missing)
        for decision in decisions
    ]
    report = build_report(
        repo_root=repo_root,
        policy_path=policy_path,
        decisions=decisions,
        results=results,
        execute=execute,
    )
    write_manifest(output_dir, report)
    if report["status"] != "ready":
        raise SystemExit(2)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive obsolete stage documentation from a KR-0B cleanup policy.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--policy-zip", type=Path, default=None, help="ZIP containing cleanup_policy.json")
    parser.add_argument("--policy-json", type=Path, default=None, help="cleanup_policy.json path")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="Move files. Without this flag the command is a dry run.")
    parser.add_argument("--allow-missing", action="store_true", help="Treat already removed source files as non-blocking.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    policy_path = args.policy_zip or args.policy_json
    if policy_path is None:
        raise SystemExit("provide --policy-zip or --policy-json")
    report = archive_obsolete_stage_docs(
        repo_root=args.repo_root.resolve(),
        policy_path=policy_path,
        output_dir=args.output_dir,
        execute=args.execute,
        allow_missing=args.allow_missing,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"[INFO] status={report['status']}")
        print(f"[INFO] decision_count={summary['decision_count']}")
        print(f"[INFO] moved_count={summary['moved_count']}")
        print(f"[INFO] planned_count={summary['planned_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
