#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.kw_archive_obsolete_stage_docs import archive_decisions, load_policy


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _markdown_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines) + "\n"


def check_archived_stage_docs(
    *,
    repo_root: Path,
    policy_path: Path,
    output_dir: Path,
    require_ready: bool,
) -> dict[str, Any]:
    policy = load_policy(policy_path)
    decisions = archive_decisions(policy)

    checks: list[dict[str, str | bool]] = []
    active_count = 0
    missing_archive_count = 0
    ready_count = 0

    for decision in decisions:
        source_path = repo_root / decision.source
        destination_path = repo_root / decision.destination
        source_exists = source_path.exists()
        destination_exists = destination_path.exists()
        if source_exists:
            active_count += 1
        if not destination_exists:
            missing_archive_count += 1
        if not source_exists and destination_exists:
            ready_count += 1
        checks.append(
            {
                "source": decision.source,
                "destination": decision.destination,
                "source_exists": source_exists,
                "destination_exists": destination_exists,
                "status": "ready" if (not source_exists and destination_exists) else "not_ready",
            }
        )

    status = "ready" if active_count == 0 and missing_archive_count == 0 else "blocked"
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "policy_path": str(policy_path),
        "status": status,
        "summary": {
            "archive_decision_count": len(decisions),
            "ready_count": ready_count,
            "active_legacy_doc_count": active_count,
            "missing_archive_count": missing_archive_count,
        },
        "checks": checks,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "archived_stage_docs_check.json", payload)
    markdown_rows = [
        (
            str(item["status"]),
            str(item["source"]),
            str(item["destination"]),
            str(item["source_exists"]),
            str(item["destination_exists"]),
        )
        for item in checks[:150]
    ]
    markdown = "\n".join(
        [
            "# Archived stage documentation check",
            "",
            _markdown_table(
                [(key, str(value)) for key, value in payload["summary"].items()],
                ("Metric", "Value"),
            ),
            "## Checks",
            "",
            _markdown_table(
                markdown_rows,
                ("Status", "Source", "Destination", "Source exists", "Archive exists"),
            ),
        ]
    )
    (output_dir / "archived_stage_docs_check.md").write_text(markdown + "\n", encoding="utf-8")

    if require_ready and status != "ready":
        raise SystemExit(2)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that KR-1B archived obsolete stage documentation.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--policy-zip", type=Path, default=None)
    parser.add_argument("--policy-json", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    policy_path = args.policy_zip or args.policy_json
    if policy_path is None:
        raise SystemExit("provide --policy-zip or --policy-json")
    payload = check_archived_stage_docs(
        repo_root=args.repo_root.resolve(),
        policy_path=policy_path,
        output_dir=args.output_dir,
        require_ready=args.require_ready,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"[INFO] status={payload['status']}")
        for key, value in payload["summary"].items():
            print(f"[INFO] {key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
