from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_rf1_3_manifest_schema_cli_requires_ready_without_bundle() -> None:
    root = repo_root()
    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_offline_bootstrap_manifest_check.py",
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

    assert payload["mode"] == "offline-bootstrap-manifest-validation"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_3"] is False
    assert payload["dependency_versions_changed_by_rf1_3"] is False
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["schema"]["kw_studio"]["branch"] == "7_Runtime_Foundation"
    assert payload["schema"]["python"]["wheelhouse_dir"] == "python/wheelhouse"
    assert payload["schema"]["npm"]["cache_dir"] == "npm/cache"
    assert payload["schema"]["docker"]["images_dir"] == "docker/images"
    assert payload["schema"]["playwright"]["browsers_dir"] == "playwright/browsers"


def test_rf1_3_manifest_validator_accepts_temporary_bundle_fixture(tmp_path: Path) -> None:
    root = repo_root()
    bundle = tmp_path / "offline_bootstrap"

    for rel in (
        "python/wheelhouse",
        "npm/cache",
        "docker/images",
        "playwright/browsers",
        "checks",
    ):
        (bundle / rel).mkdir(parents=True, exist_ok=True)

    (bundle / "README.md").write_text("temporary RF1.3 fixture\n", encoding="utf-8")
    (bundle / "python/requirements.txt").write_text((root / "requirements.txt").read_text(encoding="utf-8"), encoding="utf-8")
    (bundle / "npm/package.json").write_text((root / "frontend/package.json").read_text(encoding="utf-8"), encoding="utf-8")
    (bundle / "npm/package-lock.json").write_text((root / "frontend/package-lock.json").read_text(encoding="utf-8"), encoding="utf-8")
    (bundle / "docker/images-manifest.txt").write_text("python:3.12-slim\nnode:20-alpine\npostgres:16\n", encoding="utf-8")
    (bundle / "playwright/browsers-manifest.txt").write_text("managed-by-operator\n", encoding="utf-8")
    (bundle / "checks/sha256sums.txt").write_text("fixture\n", encoding="utf-8")
    (bundle / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1",
                "kw_studio": {
                    "commit": "fixture",
                    "branch": "7_Runtime_Foundation",
                },
                "prepared": {
                    "mode": "online_bootstrap_preparation",
                    "timestamp_utc": "2026-05-03T00:00:00Z",
                    "host": "pytest",
                },
                "python": {
                    "requirements_file": "python/requirements.txt",
                    "wheelhouse_dir": "python/wheelhouse",
                },
                "npm": {
                    "package_json": "npm/package.json",
                    "package_lock": "npm/package-lock.json",
                    "cache_dir": "npm/cache",
                },
                "docker": {
                    "images_dir": "docker/images",
                    "images_manifest": "docker/images-manifest.txt",
                },
                "playwright": {
                    "browsers_dir": "playwright/browsers",
                    "browsers_manifest": "playwright/browsers-manifest.txt",
                },
                "checks": {
                    "sha256sums": "checks/sha256sums.txt",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/kw_offline_bootstrap_manifest_check.py",
            "--repo-root",
            str(root),
            "--bundle-dir",
            str(bundle),
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
    assert payload["bundle"]["provided"] is True
    assert payload["bundle"]["validated"] is True
    assert payload["bundle"]["errors"] == []


def test_rf1_3_manifest_doc_preserves_no_runtime_or_dependency_change_policy() -> None:
    doc = (repo_root() / "docs/codex/OFFLINE_BOOTSTRAP_MANIFEST.md").read_text(encoding="utf-8")

    assert "does not download dependencies" in doc
    assert "does not change runtime behavior" in doc
    assert "Production readiness gates must not require an actual local `offline_bootstrap/` directory" in doc
    assert "RF1.4 may implement operator tooling" in doc
