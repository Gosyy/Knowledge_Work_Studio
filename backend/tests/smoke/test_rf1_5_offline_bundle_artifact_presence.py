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


def prepare_template_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "offline_bootstrap"
    result = run_tool(
        "create-template",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return bundle


def populate_artifact_payloads(bundle: Path) -> None:
    (bundle / "python/wheelhouse/kwstudio_fixture-0.0.0-py3-none-any.whl").write_text("fixture wheel\n", encoding="utf-8")
    (bundle / "npm/cache/_cacache/content-v2/sha512/fixture").parent.mkdir(parents=True, exist_ok=True)
    (bundle / "npm/cache/_cacache/content-v2/sha512/fixture").write_text("fixture npm cache\n", encoding="utf-8")
    (bundle / "docker/images/backend-python-3.12-slim.tar").write_text("fixture docker archive\n", encoding="utf-8")
    (bundle / "playwright/browsers/chromium-fixture/browser").parent.mkdir(parents=True, exist_ok=True)
    (bundle / "playwright/browsers/chromium-fixture/browser").write_text("fixture browser\n", encoding="utf-8")
    (bundle / "docker/images-manifest.txt").write_text("python:3.12-slim\nnode:20-alpine\npostgres:16\n", encoding="utf-8")
    (bundle / "playwright/browsers-manifest.txt").write_text("chromium fixture\n", encoding="utf-8")
    (bundle / "checks/sha256sums.txt").write_text("fixture  manifest.json\n", encoding="utf-8")


def test_rf1_5_artifact_policy_check_requires_ready() -> None:
    result = run_tool("check-artifact-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bundle-artifact-presence-policy"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_5"] is False
    assert payload["dependency_versions_changed_by_rf1_5"] is False
    assert payload["bundle_required_for_readiness"] is False
    assert payload["artifact_presence_requires_bundle_dir"] is True
    assert payload["runbook_commands_documented"] is True
    assert payload["errors"] == []


def test_rf1_5_verify_artifacts_fails_on_template_only_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)

    result = run_tool(
        "verify-artifacts",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["mode"] == "offline-bundle-artifact-presence-verification"
    assert payload["network_required"] is False
    assert payload["status"] == "failed"
    assert any("python_wheelhouse" in error for error in payload["errors"])
    assert any("npm_cache" in error for error in payload["errors"])
    assert any("docker_images" in error for error in payload["errors"])
    assert any("playwright_browsers" in error for error in payload["errors"])


def test_rf1_5_verify_artifacts_accepts_populated_fixture_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)
    populate_artifact_payloads(bundle)

    result = run_tool(
        "verify-artifacts",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["downloads_performed"] is False
    assert payload["package_managers_run"] is False
    assert payload["docker_pull_or_save_run"] is False
    assert payload["playwright_install_run"] is False


def test_rf1_5_print_runbook_exposes_operator_commands() -> None:
    result = run_tool("print-runbook", "--repo-root", str(repo_root()), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bootstrap-runbook-commands"
    assert payload["network_required_by_command_printer"] is False
    assert payload["commands_are_examples_only"] is True
    assert "python3 -m pip download" in payload["commands"]["python"][0]
    assert "npm ci" in payload["commands"]["npm"][0]
    assert "docker save" in "\n".join(payload["commands"]["docker"])
    assert "playwright install chromium" in payload["commands"]["playwright"][0]


def test_rf1_5_operator_runbook_documents_non_goals() -> None:
    doc = (repo_root() / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")

    assert "RF1.5 checkpoint" in doc
    assert "does not execute those commands automatically" in doc
    assert "Python wheelhouse preparation command" in doc
    assert "npm cache preparation command" in doc
    assert "Docker image preparation commands" in doc
    assert "Playwright browser preparation command" in doc
    assert "Artifact presence verification" in doc
    assert "RF1.6 handoff" in doc
