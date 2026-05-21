from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_active_gate_legacy_retirement_checker_cli_ready() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_active_gate_legacy_retirement_check.py",
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
    assert payload["retired_still_in_gate_count"] == 0
    assert payload["missing_replacement_checks_count"] == 0
    assert payload["legacy_assets_retained"] is True
