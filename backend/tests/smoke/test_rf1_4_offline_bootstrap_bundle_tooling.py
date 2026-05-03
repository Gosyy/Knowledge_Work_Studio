from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    root = repo_root()
    return subprocess.run(
        [sys.executable, "scripts/kw_offline_bootstrap_bundle_tool.py", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_rf1_4_policy_check_requires_ready() -> None:
    result = run_tool("check-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bundle-tool-policy"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_4"] is False
    assert payload["dependency_versions_changed_by_rf1_4"] is False
    assert payload["bundle_required"] is False
    assert payload["errors"] == []
    assert {"check-policy", "create-template", "verify-bundle"}.issubset(set(payload["commands"]))


def test_rf1_4_create_template_and_verify_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "offline_bootstrap"

    create = run_tool(
        "create-template",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
    )
    assert create.returncode == 0, create.stdout + create.stderr
    create_payload = json.loads(create.stdout)
    assert create_payload["created"] is True
    assert create_payload["network_required"] is False
    assert create_payload["downloads_performed"] is False
    assert create_payload["package_managers_run"] is False
    assert create_payload["docker_pull_or_save_run"] is False
    assert create_payload["playwright_install_run"] is False
    assert create_payload["errors"] == []

    for rel in (
        "README.md",
        "manifest.json",
        "python/requirements.txt",
        "python/wheelhouse",
        "npm/package.json",
        "npm/package-lock.json",
        "npm/cache",
        "docker/images",
        "docker/images-manifest.txt",
        "playwright/browsers",
        "playwright/browsers-manifest.txt",
        "checks/sha256sums.txt",
    ):
        assert (bundle / rel).exists(), rel

    verify = run_tool(
        "verify-bundle",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr
    verify_payload = json.loads(verify.stdout)
    assert verify_payload["mode"] == "offline-bundle-verification"
    assert verify_payload["network_required"] is False
    assert verify_payload["status"] == "ready"
    assert verify_payload["errors"] == []


def test_rf1_4_tooling_doc_and_gitignore_policy() -> None:
    root = repo_root()
    doc = (root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md").read_text(encoding="utf-8")
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")

    assert "RF1.4 checkpoint" in doc
    assert "does not download dependencies" in doc
    assert "change runtime behavior" in doc
    assert "RF1.5 handoff" in doc
    assert "offline_bootstrap/" in gitignore
