from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_controlled_archive_delete_readiness_checker_cli_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_controlled_archive_delete_readiness_check.py",
            "--repo-root",
            str(REPO_ROOT),
            "--json",
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["moved_paths_count"] >= 1
    assert payload["active_old_path_references_count"] == 0
    assert payload["docs_codex_files_still_present_count"] > 0
