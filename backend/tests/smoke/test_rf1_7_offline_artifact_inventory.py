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
    (bundle / "docker/images/python-3.12-slim.tar").write_text("fixture python image\n", encoding="utf-8")
    (bundle / "docker/images/node-20-alpine.tar").write_text("fixture node image\n", encoding="utf-8")
    (bundle / "docker/images/postgres-16.tar").write_text("fixture postgres image\n", encoding="utf-8")
    (bundle / "playwright/browsers/chromium-fixture/browser").parent.mkdir(parents=True, exist_ok=True)
    (bundle / "playwright/browsers/chromium-fixture/browser").write_text("fixture browser\n", encoding="utf-8")
    (bundle / "docker/images-manifest.txt").write_text("python:3.12-slim\nnode:20-alpine\npostgres:16\n", encoding="utf-8")
    (bundle / "playwright/browsers-manifest.txt").write_text("chromium fixture\n", encoding="utf-8")


def test_rf1_7_inventory_policy_check_requires_ready() -> None:
    result = run_tool("check-inventory-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-artifact-inventory-policy"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_7"] is False
    assert payload["dependency_versions_changed_by_rf1_7"] is False
    assert payload["bundle_required_for_readiness"] is False
    assert payload["inventory_summary_requires_bundle_dir"] is True
    assert payload["expected_profile_available"] is True
    assert {"python:3.12-slim", "node:20-alpine", "postgres:16"}.issubset(set(payload["expected_docker_images"]))
    assert payload["errors"] == []


def test_rf1_7_expected_profile_lists_current_dependency_surfaces() -> None:
    result = run_tool("expected-profile", "--repo-root", str(repo_root()), "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    profile = payload["profile"]

    assert payload["mode"] == "offline-expected-profile"
    assert payload["network_required"] is False
    assert "fastapi" in profile["python"]["normalized_direct_names"]
    assert profile["npm"]["dependencies"]["next"] == "14.2.35"
    assert profile["npm"]["dependencies"]["react"] == "18.3.1"
    assert {"python:3.12-slim", "node:20-alpine", "postgres:16"}.issubset(set(profile["docker"]["expected_images"]))
    assert profile["playwright"]["declared"] is True


def test_rf1_7_inventory_summary_accepts_template_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)

    result = run_tool(
        "inventory-summary",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-artifact-inventory-summary"
    assert payload["network_required"] is False
    assert payload["status"] == "ready"
    assert payload["python_wheelhouse"]["file_count"] == 0
    assert payload["npm_cache"]["file_count"] == 0
    assert payload["docker_images"]["file_count"] == 0
    assert payload["playwright_browsers"]["file_count"] == 0
    assert payload["docker_images_manifest"]["missing_expected_images"] == []


def test_rf1_7_inventory_summary_reports_populated_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)
    populate_artifact_payloads(bundle)

    result = run_tool(
        "inventory-summary",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["status"] == "ready"
    assert payload["python_wheelhouse"]["file_count"] == 1
    assert payload["npm_cache"]["file_count"] == 1
    assert payload["docker_images"]["file_count"] == 3
    assert payload["playwright_browsers"]["file_count"] == 1
    assert {"python:3.12-slim", "node:20-alpine", "postgres:16"}.issubset(
        set(payload["docker_images_manifest"]["entries"])
    )


def test_rf1_7_inventory_summary_fails_when_expected_docker_image_is_missing(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)
    (bundle / "docker/images-manifest.txt").write_text("python:3.12-slim\n", encoding="utf-8")

    result = run_tool(
        "inventory-summary",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert "node:20-alpine" in payload["docker_images_manifest"]["missing_expected_images"]
    assert "postgres:16" in payload["docker_images_manifest"]["missing_expected_images"]


def test_rf1_7_docs_are_present() -> None:
    root = repo_root()
    inventory = (root / "docs/codex/OFFLINE_BOOTSTRAP_ARTIFACT_INVENTORY.md").read_text(encoding="utf-8")
    runbook = (root / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    tooling = (root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md").read_text(encoding="utf-8")

    assert "RF1.7 checkpoint" in inventory
    assert "Expected profile" in inventory
    assert "inventory-summary" in inventory
    assert "expected-profile" in inventory
    assert "RF1.8 handoff" in inventory
    assert "RF1.7 artifact inventory commands" in runbook
    assert "RF1.7 artifact inventory summaries" in tooling
