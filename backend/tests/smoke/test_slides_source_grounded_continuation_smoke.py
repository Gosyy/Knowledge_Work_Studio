from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_kr6a_slides_source_grounded_checker_ready(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_slides_source_grounded_continuation_check.py",
            "--repo-root",
            str(REPO_ROOT),
            "--output-dir",
            str(tmp_path),
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
    assert payload["summary"]["all_slides_have_citations"] is True
    assert (tmp_path / "kr6a_slides_source_grounded_bundle" / "citation_manifest.json").exists()


def test_kr6a_production_gate_includes_slides_source_grounded_guardrail() -> None:
    gate_text = (REPO_ROOT / "scripts" / "kw_production_readiness_gate.py").read_text(encoding="utf-8")
    assert "KR-6A source-grounded Slides continuation" in gate_text
    assert "scripts/kw_slides_source_grounded_continuation_check.py" in gate_text
