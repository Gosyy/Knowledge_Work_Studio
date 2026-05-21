from __future__ import annotations

import hashlib
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


def populate_artifact_payloads(bundle: Path) -> list[str]:
    files = {
        "python/wheelhouse/kwstudio_fixture-0.0.0-py3-none-any.whl": "fixture wheel\n",
        "npm/cache/_cacache/content-v2/sha512/fixture": "fixture npm cache\n",
        "docker/images/python-3.12-slim.tar": "fixture python image\n",
        "docker/images/node-20-alpine.tar": "fixture node image\n",
        "docker/images/postgres-16.tar": "fixture postgres image\n",
        "playwright/browsers/chromium-fixture/browser": "fixture browser\n",
        "docker/images-manifest.txt": "python:3.12-slim\nnode:20-alpine\npostgres:16\n",
        "playwright/browsers-manifest.txt": "chromium fixture\n",
    }
    for rel, content in files.items():
        path = bundle / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return sorted(files)


def write_checksums(bundle: Path, rel_paths: list[str]) -> None:
    lines = []
    for rel in rel_paths:
        payload = (bundle / rel).read_bytes()
        lines.append(f"{hashlib.sha256(payload).hexdigest()}  {rel}")
    (bundle / "checks/sha256sums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepare_ready_bundle(tmp_path: Path) -> Path:
    bundle = prepare_template_bundle(tmp_path)
    rel_paths = populate_artifact_payloads(bundle)
    write_checksums(bundle, rel_paths)
    return bundle


def test_rf1_8_readiness_policy_check_requires_ready() -> None:
    result = run_tool("check-readiness-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bundle-readiness-report-policy"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_8"] is False
    assert payload["dependency_versions_changed_by_rf1_8"] is False
    assert payload["bundle_required_for_readiness"] is False
    assert payload["bundle_readiness_report_requires_bundle_dir"] is True
    assert payload["offline_build_dry_run_available"] is True
    assert payload["dry_run_step_count"] >= 6
    assert payload["errors"] == []


def test_rf1_8_offline_build_dry_run_prints_recipe_without_execution(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)

    result = run_tool(
        "offline-build-dry-run",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-build-dry-run"
    assert payload["network_required"] is False
    assert payload["commands_are_not_executed"] is True
    assert payload["runtime_changed_by_rf1_8"] is False
    assert payload["dependency_versions_changed_by_rf1_8"] is False
    step_ids = {step["step_id"] for step in payload["steps"]}
    assert "verify_bundle_layout" in step_ids
    assert "verify_artifact_presence" in step_ids
    assert "verify_checksums" in step_ids
    assert "review_inventory" in step_ids
    assert "runtime_smoke_skip_build" in step_ids


def test_rf1_8_bundle_readiness_report_accepts_ready_bundle(tmp_path: Path) -> None:
    bundle = prepare_ready_bundle(tmp_path)

    result = run_tool(
        "bundle-readiness-report",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bundle-readiness-report"
    assert payload["network_required"] is False
    assert payload["commands_executed"] is False
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["sections"]["layout"]["status"] == "ready"
    assert payload["sections"]["artifact_presence"]["status"] == "ready"
    assert payload["sections"]["checksum_integrity"]["status"] == "ready"
    assert payload["sections"]["inventory"]["status"] == "ready"
    assert payload["sections"]["dry_run_recipe"]["commands_are_not_executed"] is True


def test_rf1_8_bundle_readiness_report_rejects_template_only_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)

    result = run_tool(
        "bundle-readiness-report",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)

    assert payload["status"] == "failed"
    assert payload["sections"]["layout"]["status"] == "ready"
    assert payload["sections"]["artifact_presence"]["status"] == "failed"
    assert payload["sections"]["checksum_integrity"]["status"] == "failed"
    assert any("artifact_presence" in error for error in payload["errors"])
    assert any("checksum_integrity" in error for error in payload["errors"])


def test_rf1_8_bundle_readiness_report_rejects_corrupted_checksum(tmp_path: Path) -> None:
    bundle = prepare_ready_bundle(tmp_path)
    (bundle / "docker/images/node-20-alpine.tar").write_text("corrupted image\n", encoding="utf-8")

    result = run_tool(
        "bundle-readiness-report",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["sections"]["checksum_integrity"]["status"] == "failed"
    assert any("checksum mismatch" in error for error in payload["errors"])


def test_rf1_8_docs_are_present() -> None:
    root = repo_root()
    build = (root / "docs/codex/OFFLINE_BOOTSTRAP_BUILD_READINESS.md").read_text(encoding="utf-8")
    runbook = (root / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    tooling = (root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md").read_text(encoding="utf-8")

    assert "RF1.8 checkpoint" in build
    assert "bundle-readiness-report" in build
    assert "offline-build-dry-run" in build
    assert "RF1.9 handoff" in build
    assert "RF1.8 bundle readiness report and dry-run commands" in runbook
    assert "RF1.8 bundle readiness report and offline build dry-run" in tooling
