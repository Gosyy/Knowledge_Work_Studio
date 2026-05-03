from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rf1_offline_dependency_inventory_cli_requires_ready() -> None:
    root = repo_root()
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_offline_dependency_inventory_check.py",
            "--repo-root",
            str(root),
            "--require-ready",
            "--json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    inventory = payload["inventory"]

    assert payload["errors"] == []
    assert inventory["mode"] == "offline-no-network-inventory"
    assert inventory["network_required"] is False
    assert inventory["runtime_changed_by_rf1_1"] is False
    assert inventory["status"] in {"ready", "ready_with_followups"}

    assert "fastapi" in inventory["python"]["normalized_direct_names"]
    assert inventory["frontend"]["dependencies"]["next"] == "14.2.35"
    assert inventory["docker"]["backend_uses_requirements_install"] is True
    assert inventory["docker"]["frontend_uses_npm_ci"] is True
    assert "postgres:16" in inventory["docker"]["compose_images"]
    assert inventory["browser_e2e"]["playwright_declared"] is True


def test_rf1_policy_doc_names_followup_surfaces() -> None:
    doc = (repo_root() / "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md").read_text(encoding="utf-8")

    assert "Python wheelhouse" in doc
    assert "npm cache" in doc
    assert "Docker base image export/import" in doc
    assert "Playwright browser binary cache" in doc
    assert "Direct local GigaChat remains the default production LLM path" in doc
