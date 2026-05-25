import json
import subprocess
import sys
from pathlib import Path


def test_assistant_governance_check_reports_ready() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_assistant_governance_check.py",
            "--repo-root",
            ".",
            "--json",
            "--require-ready",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "ready"
    assert report["issues"] == []
