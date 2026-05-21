from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_project_migration_handoff_smoke_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_project_migration_handoff_check.py",
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
    assert payload["issues"] == []
