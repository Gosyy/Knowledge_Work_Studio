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
        "docker/images/backend-python-3.12-slim.tar": "fixture docker archive\n",
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


def test_rf1_6_integrity_policy_check_requires_ready() -> None:
    result = run_tool("check-integrity-policy", "--repo-root", str(repo_root()), "--require-ready", "--json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    assert payload["mode"] == "offline-bundle-checksum-integrity-policy"
    assert payload["network_required"] is False
    assert payload["runtime_changed_by_rf1_6"] is False
    assert payload["dependency_versions_changed_by_rf1_6"] is False
    assert payload["bundle_required_for_readiness"] is False
    assert payload["checksum_verification_requires_bundle_dir"] is True
    assert payload["checksum_file"] == "checks/sha256sums.txt"
    assert payload["hash_algorithm"] == "sha256"
    assert payload["errors"] == []


def test_rf1_6_verify_checksums_accepts_valid_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)
    rel_paths = populate_artifact_payloads(bundle)
    write_checksums(bundle, rel_paths)

    result = run_tool(
        "verify-checksums",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "offline-bundle-checksum-verification"
    assert payload["network_required"] is False
    assert payload["status"] == "ready"
    assert payload["errors"] == []
    assert payload["mismatches"] == []
    assert payload["checked_file_count"] == len(rel_paths)


def test_rf1_6_verify_checksums_rejects_corrupted_bundle(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)
    rel_paths = populate_artifact_payloads(bundle)
    write_checksums(bundle, rel_paths)

    target = bundle / "python/wheelhouse/kwstudio_fixture-0.0.0-py3-none-any.whl"
    target.write_text("corrupted wheel\n", encoding="utf-8")

    result = run_tool(
        "verify-checksums",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert any("checksum mismatch" in error for error in payload["errors"])
    assert "python/wheelhouse/kwstudio_fixture-0.0.0-py3-none-any.whl" in payload["mismatches"]


def test_rf1_6_verify_checksums_rejects_parent_traversal(tmp_path: Path) -> None:
    bundle = prepare_template_bundle(tmp_path)
    populate_artifact_payloads(bundle)
    (bundle / "checks/sha256sums.txt").write_text(
        "0" * 64 + "  ../outside.txt\n",
        encoding="utf-8",
    )

    result = run_tool(
        "verify-checksums",
        "--repo-root",
        str(repo_root()),
        "--bundle-dir",
        str(bundle),
        "--json",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert any("parent traversal is not allowed" in error for error in payload["errors"])


def test_rf1_6_integrity_doc_and_runbook_are_present() -> None:
    root = repo_root()
    integrity = (root / "docs/codex/OFFLINE_BOOTSTRAP_INTEGRITY.md").read_text(encoding="utf-8")
    runbook = (root / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    tooling = (root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md").read_text(encoding="utf-8")

    assert "RF1.6 checkpoint" in integrity
    assert "verify-checksums" in integrity
    assert "checks/sha256sums.txt" in integrity
    assert "RF1.7 handoff" in integrity
    assert "RF1.6 checksum verification commands" in runbook
    assert "find . -type f ! -path './checks/sha256sums.txt'" in runbook
    assert "RF1.6 checksum and integrity verification" in tooling
