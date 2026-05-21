#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_REPO_FILES = (
    "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_MANIFEST.md",
    "requirements.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/playwright.config.ts",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
)

REQUIRED_DOC_PHRASES = (
    "RF1.3 checkpoint",
    "Default readiness behavior",
    "Operator bundle validation behavior",
    "Manifest schema",
    "Allowed preparation modes",
    "Git hygiene policy",
    "RF1.4 handoff",
)

EXPECTED_BUNDLE_PATHS = (
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
)

ALLOWED_PREPARATION_MODES = {
    "online_bootstrap_preparation",
    "intranet_mirror_preparation",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def current_git_commit(repo_root: Path) -> str | None:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def expected_schema(repo_root: Path) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "kw_studio": {
            "commit": current_git_commit(repo_root) or "<git commit sha>",
            "branch": "7_Runtime_Foundation",
        },
        "prepared": {
            "mode_values": sorted(ALLOWED_PREPARATION_MODES),
            "timestamp_utc": "<ISO-8601 timestamp>",
            "host": "<operator host summary>",
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
    }


def validate_repo_policy(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_REPO_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing required RF1.3 surface: {rel}")

    doc_path = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_MANIFEST.md"
    if doc_path.exists():
        doc = read_text(doc_path)
        for phrase in REQUIRED_DOC_PHRASES:
            if phrase not in doc:
                errors.append(f"offline bootstrap manifest doc is missing phrase: {phrase}")

    if require_ready and (repo_root / "offline_bootstrap").exists():
        errors.append("operator offline_bootstrap/ directory must not be present in repo root during readiness")

    return errors


def require_manifest_object(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("manifest must be a JSON object")
    return payload


def validate_manifest_json(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if str(manifest.get("schema_version")) != "1":
        errors.append("manifest schema_version must be '1'")

    kw_studio = manifest.get("kw_studio")
    if not isinstance(kw_studio, dict):
        errors.append("manifest kw_studio must be an object")
    else:
        if not str(kw_studio.get("commit", "")).strip():
            errors.append("manifest kw_studio.commit is required")
        branch = str(kw_studio.get("branch", "")).strip()
        if branch != "7_Runtime_Foundation":
            errors.append("manifest kw_studio.branch must be 7_Runtime_Foundation for RF1.x bundles")

    prepared = manifest.get("prepared")
    if not isinstance(prepared, dict):
        errors.append("manifest prepared must be an object")
    else:
        mode = str(prepared.get("mode", "")).strip()
        if mode not in ALLOWED_PREPARATION_MODES:
            errors.append(
                "manifest prepared.mode must be one of: "
                + ", ".join(sorted(ALLOWED_PREPARATION_MODES))
            )
        if not str(prepared.get("timestamp_utc", "")).strip():
            errors.append("manifest prepared.timestamp_utc is required")

    required_sections = {
        "python": ("requirements_file", "wheelhouse_dir"),
        "npm": ("package_json", "package_lock", "cache_dir"),
        "docker": ("images_dir", "images_manifest"),
        "playwright": ("browsers_dir", "browsers_manifest"),
        "checks": ("sha256sums",),
    }
    for section, keys in required_sections.items():
        value = manifest.get(section)
        if not isinstance(value, dict):
            errors.append(f"manifest {section} must be an object")
            continue
        for key in keys:
            if not str(value.get(key, "")).strip():
                errors.append(f"manifest {section}.{key} is required")

    return errors


def validate_bundle_dir(bundle_dir: Path) -> list[str]:
    errors: list[str] = []

    if not bundle_dir.exists():
        return [f"bundle directory does not exist: {bundle_dir}"]
    if not bundle_dir.is_dir():
        return [f"bundle path is not a directory: {bundle_dir}"]

    for rel in EXPECTED_BUNDLE_PATHS:
        path = bundle_dir / rel
        if not path.exists():
            errors.append(f"bundle is missing expected path: {rel}")

    manifest_path = bundle_dir / "manifest.json"
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = require_manifest_object(payload)
        except Exception as exc:  # noqa: BLE001 - CLI validation should report any JSON/schema issue.
            errors.append(f"manifest.json is not valid JSON object: {exc}")
        else:
            errors.extend(validate_manifest_json(manifest))

    return errors


def build_report(repo_root: Path, bundle_dir: Path | None, require_ready: bool) -> dict[str, Any]:
    schema = expected_schema(repo_root)
    errors = validate_repo_policy(repo_root, require_ready=require_ready)

    bundle_report: dict[str, Any] = {
        "provided": bundle_dir is not None,
        "path": str(bundle_dir) if bundle_dir else None,
        "validated": False,
        "errors": [],
    }
    if bundle_dir is not None:
        bundle_errors = validate_bundle_dir(bundle_dir)
        bundle_report["validated"] = not bundle_errors
        bundle_report["errors"] = bundle_errors
        errors.extend(bundle_errors)

    return {
        "mode": "offline-bootstrap-manifest-validation",
        "network_required": False,
        "runtime_changed_by_rf1_3": False,
        "dependency_versions_changed_by_rf1_3": False,
        "schema": schema,
        "bundle": bundle_report,
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KW Studio RF1.3 offline bootstrap manifest and bundle validation.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root path.")
    parser.add_argument("--bundle-dir", default=None, help="Optional offline_bootstrap bundle directory to validate.")
    parser.add_argument("--require-ready", action="store_true", help="Require repository readiness policy.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    bundle_dir = Path(args.bundle_dir).expanduser().resolve() if args.bundle_dir else None
    report = build_report(repo_root, bundle_dir, require_ready=args.require_ready)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        if bundle_dir:
            print(f"[INFO] bundle_dir={bundle_dir}")
        print("[offline-bootstrap-manifest-validation]")
        print(json.dumps(report, indent=2, sort_keys=True))

    if report["errors"]:
        for error in report["errors"]:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 2

    if not args.json:
        print("[PASS] offline bootstrap manifest validation completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
