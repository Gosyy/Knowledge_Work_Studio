from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rf1_2_offline_bootstrap_bundle_strategy_cli_requires_ready() -> None:
    root = repo_root()
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_offline_bootstrap_bundle_check.py",
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
    strategy = payload["strategy"]

    assert payload["errors"] == []
    assert strategy["mode"] == "offline-bootstrap-bundle-strategy"
    assert strategy["network_required"] is False
    assert strategy["runtime_changed_by_rf1_2"] is False
    assert strategy["dependency_versions_changed_by_rf1_2"] is False
    assert strategy["canonical_bundle_root"] == "offline_bootstrap"
    assert "python:3.12-slim" in strategy["docker_images"]
    assert "node:20-alpine" in strategy["docker_images"]
    assert "postgres:16" in strategy["docker_images"]
    assert strategy["bundle_sections"]["python"] == "offline_bootstrap/python/wheelhouse"
    assert strategy["bundle_sections"]["npm"] == "offline_bootstrap/npm/cache"
    assert strategy["bundle_sections"]["docker"] == "offline_bootstrap/docker/images"
    assert strategy["bundle_sections"]["playwright"] == "offline_bootstrap/playwright/browsers"


def test_rf1_2_strategy_doc_separates_bootstrap_and_runtime_modes() -> None:
    doc = (repo_root() / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md").read_text(encoding="utf-8")

    assert "online bootstrap preparation" in doc
    assert "offline build" in doc
    assert "offline runtime" in doc
    assert "must not be confused with default production runtime" in doc
    assert "Direct local GigaChat remains the default production LLM path" in doc
    assert "RF1.3 may implement operator tooling" in doc
