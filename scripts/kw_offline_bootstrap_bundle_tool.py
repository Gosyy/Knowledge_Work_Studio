#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_POLICY_FILES = (
    "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_MANIFEST.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md",
    "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md",
    "docs/codex/OFFLINE_BOOTSTRAP_INTEGRITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_ARTIFACT_INVENTORY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUILD_READINESS.md",
    "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md",
    "scripts/kw_offline_bootstrap_manifest_check.py",
    "requirements.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/playwright.config.ts",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
)

EXPECTED_TEMPLATE_PATHS = (
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

ARTIFACT_PRESENCE_RULES = {
    "python_wheelhouse": {
        "path": "python/wheelhouse",
        "kind": "dir_non_empty",
        "description": "Python wheelhouse must contain downloaded wheel or source distribution files.",
    },
    "npm_cache": {
        "path": "npm/cache",
        "kind": "dir_non_empty",
        "description": "npm cache or local registry artifact directory must not be empty.",
    },
    "docker_images": {
        "path": "docker/images",
        "kind": "dir_non_empty",
        "description": "Docker image archive directory must not be empty.",
    },
    "playwright_browsers": {
        "path": "playwright/browsers",
        "kind": "dir_non_empty",
        "description": "Playwright browser cache directory must not be empty.",
    },
    "docker_images_manifest": {
        "path": "docker/images-manifest.txt",
        "kind": "file_non_empty",
        "description": "Docker image manifest must list prepared images.",
    },
    "playwright_browsers_manifest": {
        "path": "playwright/browsers-manifest.txt",
        "kind": "file_non_empty",
        "description": "Playwright browser manifest must describe prepared browser cache.",
    },
    "checksums": {
        "path": "checks/sha256sums.txt",
        "kind": "file_non_empty",
        "description": "Checksum inventory must exist and be non-empty.",
    },
}

RF1_CHECKPOINTS = (
    "RF1.1 dependency inventory and reproducibility policy",
    "RF1.2 offline bootstrap bundle strategy",
    "RF1.3 manifest schema and validation",
    "RF1.4 template generation and bundle verification CLI",
    "RF1.5 artifact presence checks and operator runbook commands",
    "RF1.6 checksum and artifact integrity verification",
    "RF1.7 artifact inventory summaries and expected profile",
    "RF1.8 build recipe dry-run and bundle readiness report",
    "RF1.9 operator command groups and RF1 closure checkpoint",
)

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def copy_text_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def git_output(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def current_branch(repo_root: Path) -> str:
    return git_output(repo_root, "branch", "--show-current") or "unknown"


def current_commit(repo_root: Path) -> str:
    return git_output(repo_root, "rev-parse", "HEAD") or "unknown"


def collect_docker_from_images(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*FROM\s+([^\s]+)", text)


def collect_compose_images(text: str) -> list[str]:
    return re.findall(r"(?im)(?:^|\s)image:\s*([A-Za-z0-9_./:-]+)", text)


def current_docker_images(repo_root: Path) -> list[str]:
    images = set()
    images.update(collect_docker_from_images(read_text(repo_root / "Dockerfile.backend")))
    images.update(collect_docker_from_images(read_text(repo_root / "frontend/Dockerfile")))
    images.update(collect_compose_images(read_text(repo_root / "docker-compose.deploy.yml")))
    return sorted(images)


def parse_requirements(repo_root: Path) -> list[str]:
    requirements: list[str] = []
    for raw_line in read_text(repo_root / "requirements.txt").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def normalize_requirement_name(requirement: str) -> str:
    cleaned = requirement.split(";", 1)[0].strip()
    cleaned = re.split(r"[<>=!~\[]", cleaned, maxsplit=1)[0].strip()
    return cleaned.lower().replace("_", "-")


def frontend_package(repo_root: Path) -> dict[str, Any]:
    return json.loads(read_text(repo_root / "frontend/package.json"))


def expected_offline_profile(repo_root: Path) -> dict[str, Any]:
    package = frontend_package(repo_root)
    direct_requirements = parse_requirements(repo_root)
    return {
        "python": {
            "source": "requirements.txt",
            "direct_requirements": direct_requirements,
            "normalized_direct_names": sorted({normalize_requirement_name(item) for item in direct_requirements}),
        },
        "npm": {
            "source": "frontend/package.json",
            "package": package.get("name"),
            "dependencies": package.get("dependencies", {}),
            "dev_dependencies": package.get("devDependencies", {}),
            "scripts": package.get("scripts", {}),
            "lock_source": "frontend/package-lock.json",
        },
        "docker": {
            "sources": ["Dockerfile.backend", "frontend/Dockerfile", "docker-compose.deploy.yml"],
            "expected_images": current_docker_images(repo_root),
        },
        "playwright": {
            "source": "frontend/playwright.config.ts",
            "declared": (repo_root / "frontend/playwright.config.ts").exists(),
        },
        "network_required": False,
        "runtime_changed_by_rf1_7": False,
        "dependency_versions_changed_by_rf1_7": False,
    }


def build_manifest_template(repo_root: Path, mode: str) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "kw_studio": {
            "commit": current_commit(repo_root),
            "branch": current_branch(repo_root),
        },
        "prepared": {
            "mode": mode,
            "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
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
            "images": current_docker_images(repo_root),
        },
        "playwright": {
            "browsers_dir": "playwright/browsers",
            "browsers_manifest": "playwright/browsers-manifest.txt",
        },
        "checks": {
            "sha256sums": "checks/sha256sums.txt",
        },
        "rf1": {
            "template_only": True,
            "downloads_performed": False,
            "package_managers_run": False,
            "docker_pull_or_save_run": False,
            "playwright_install_run": False,
        },
    }


def validate_manifest_payload(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["manifest must be a JSON object"]

    if str(payload.get("schema_version")) != "1":
        errors.append("manifest schema_version must be '1'")

    kw_studio = payload.get("kw_studio")
    if not isinstance(kw_studio, dict):
        errors.append("manifest kw_studio must be an object")
    else:
        if not str(kw_studio.get("commit", "")).strip():
            errors.append("manifest kw_studio.commit is required")
        if str(kw_studio.get("branch", "")).strip() != "7_Runtime_Foundation":
            errors.append("manifest kw_studio.branch must be 7_Runtime_Foundation")

    prepared = payload.get("prepared")
    if not isinstance(prepared, dict):
        errors.append("manifest prepared must be an object")
    else:
        mode = str(prepared.get("mode", "")).strip()
        if mode not in ALLOWED_PREPARATION_MODES:
            errors.append(
                "manifest prepared.mode must be one of: "
                + ", ".join(sorted(ALLOWED_PREPARATION_MODES))
            )

    required = {
        "python": ("requirements_file", "wheelhouse_dir"),
        "npm": ("package_json", "package_lock", "cache_dir"),
        "docker": ("images_dir", "images_manifest"),
        "playwright": ("browsers_dir", "browsers_manifest"),
        "checks": ("sha256sums",),
    }
    for section, keys in required.items():
        value = payload.get(section)
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

    for rel in EXPECTED_TEMPLATE_PATHS:
        if not (bundle_dir / rel).exists():
            errors.append(f"bundle is missing expected path: {rel}")

    manifest_path = bundle_dir / "manifest.json"
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"manifest.json is invalid JSON: {exc}")
        else:
            errors.extend(validate_manifest_payload(payload))

    return errors


def _has_payload(path: Path) -> bool:
    if path.is_file():
        return path.stat().st_size > 0
    if path.is_dir():
        return any(child.is_file() and child.stat().st_size > 0 for child in path.rglob("*"))
    return False


def validate_artifact_presence(bundle_dir: Path) -> list[str]:
    errors = validate_bundle_dir(bundle_dir)

    for name, rule in ARTIFACT_PRESENCE_RULES.items():
        path = bundle_dir / str(rule["path"])
        if rule["kind"] == "dir_non_empty":
            if not path.is_dir():
                errors.append(f"{name}: expected non-empty directory at {rule['path']}")
            elif not _has_payload(path):
                errors.append(f"{name}: directory is empty or contains no non-empty files at {rule['path']}")
        elif rule["kind"] == "file_non_empty":
            if not path.is_file():
                errors.append(f"{name}: expected non-empty file at {rule['path']}")
            elif path.stat().st_size <= 0:
                errors.append(f"{name}: file is empty at {rule['path']}")

    return errors


def _normalize_checksum_path(raw_path: str) -> str:
    value = raw_path.strip()
    if value.startswith("*"):
        value = value[1:]
    if value.startswith("./"):
        value = value[2:]
    return value


def parse_sha256sums(bundle_dir: Path) -> tuple[list[dict[str, str]], list[str]]:
    checksum_path = bundle_dir / "checks/sha256sums.txt"
    errors: list[str] = []
    entries: list[dict[str, str]] = []

    if not checksum_path.exists():
        return entries, ["missing checksum file: checks/sha256sums.txt"]
    if checksum_path.stat().st_size <= 0:
        return entries, ["checksum file is empty: checks/sha256sums.txt"]

    for line_number, raw_line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = re.match(r"^([0-9a-fA-F]{64})\s+(.+)$", line)
        if not match:
            errors.append(f"checks/sha256sums.txt:{line_number}: malformed sha256sum entry")
            continue

        digest = match.group(1).lower()
        rel_path = _normalize_checksum_path(match.group(2))
        if not rel_path:
            errors.append(f"checks/sha256sums.txt:{line_number}: empty relative path")
            continue
        if Path(rel_path).is_absolute():
            errors.append(f"checks/sha256sums.txt:{line_number}: absolute paths are not allowed: {rel_path}")
            continue
        if ".." in Path(rel_path).parts:
            errors.append(f"checks/sha256sums.txt:{line_number}: parent traversal is not allowed: {rel_path}")
            continue
        if rel_path == "checks/sha256sums.txt":
            errors.append(f"checks/sha256sums.txt:{line_number}: checksum file must not include itself")
            continue
        if not SHA256_RE.match(digest):
            errors.append(f"checks/sha256sums.txt:{line_number}: invalid sha256 digest")
            continue

        entries.append({"sha256": digest, "path": rel_path})

    if not entries and not errors:
        errors.append("checksum file contains no checksum entries")

    return entries, errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_checksums(bundle_dir: Path) -> dict[str, Any]:
    errors = validate_bundle_dir(bundle_dir)
    entries, parse_errors = parse_sha256sums(bundle_dir)
    errors.extend(parse_errors)

    checked: list[str] = []
    mismatches: list[str] = []

    for entry in entries:
        rel_path = entry["path"]
        expected = entry["sha256"]
        target = bundle_dir / rel_path
        if not target.exists():
            errors.append(f"checksum target is missing: {rel_path}")
            continue
        if not target.is_file():
            errors.append(f"checksum target is not a file: {rel_path}")
            continue

        actual = sha256_file(target)
        checked.append(rel_path)
        if actual != expected:
            mismatches.append(rel_path)
            errors.append(f"checksum mismatch for {rel_path}: expected {expected}, got {actual}")

    return {
        "checked_files": checked,
        "checked_file_count": len(checked),
        "mismatches": mismatches,
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def _read_manifest_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]


def summarize_path(path: Path, bundle_dir: Path, limit: int = 50) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "file_count": 0, "total_bytes": 0, "files": []}
    if path.is_file():
        rel = path.relative_to(bundle_dir).as_posix()
        return {
            "exists": True,
            "file_count": 1,
            "total_bytes": path.stat().st_size,
            "files": [{"path": rel, "bytes": path.stat().st_size}],
        }

    files = sorted(child for child in path.rglob("*") if child.is_file())
    entries = [
        {"path": child.relative_to(bundle_dir).as_posix(), "bytes": child.stat().st_size}
        for child in files[:limit]
    ]
    return {
        "exists": True,
        "file_count": len(files),
        "total_bytes": sum(child.stat().st_size for child in files),
        "files": entries,
        "truncated": len(files) > limit,
    }


def inventory_summary(repo_root: Path, bundle_dir: Path) -> dict[str, Any]:
    errors = validate_bundle_dir(bundle_dir)
    profile = expected_offline_profile(repo_root)
    expected_images = set(profile["docker"]["expected_images"])
    manifest_entries = _read_manifest_lines(bundle_dir / "docker/images-manifest.txt")
    manifest_set = set(manifest_entries)
    missing_expected_images = sorted(expected_images.difference(manifest_set))

    checksum_entries, checksum_parse_errors = parse_sha256sums(bundle_dir)
    checksum_summary = {
        "entry_count": len(checksum_entries),
        "parse_errors": checksum_parse_errors,
    }

    summary = {
        "mode": "offline-artifact-inventory-summary",
        "bundle_dir": str(bundle_dir),
        "network_required": False,
        "runtime_changed_by_rf1_7": False,
        "dependency_versions_changed_by_rf1_7": False,
        "expected_profile": profile,
        "python_wheelhouse": summarize_path(bundle_dir / "python/wheelhouse", bundle_dir),
        "npm_cache": summarize_path(bundle_dir / "npm/cache", bundle_dir),
        "docker_images": summarize_path(bundle_dir / "docker/images", bundle_dir),
        "docker_images_manifest": {
            "path": "docker/images-manifest.txt",
            "entries": manifest_entries,
            "missing_expected_images": missing_expected_images,
        },
        "playwright_browsers": summarize_path(bundle_dir / "playwright/browsers", bundle_dir),
        "playwright_browsers_manifest": {
            "path": "playwright/browsers-manifest.txt",
            "entries": _read_manifest_lines(bundle_dir / "playwright/browsers-manifest.txt"),
        },
        "checksums": checksum_summary,
        "copied_sources": {
            "requirements": summarize_path(bundle_dir / "python/requirements.txt", bundle_dir),
            "package_json": summarize_path(bundle_dir / "npm/package.json", bundle_dir),
            "package_lock": summarize_path(bundle_dir / "npm/package-lock.json", bundle_dir),
        },
    }

    errors.extend(f"docker images manifest is missing expected image: {image}" for image in missing_expected_images)
    summary["errors"] = errors
    summary["status"] = "ready" if not errors else "failed"
    return summary


def offline_build_recipe(repo_root: Path, bundle_dir: Path | None = None) -> dict[str, Any]:
    bundle_arg = str(bundle_dir) if bundle_dir else "/path/to/offline_bootstrap"
    return {
        "mode": "offline-build-dry-run",
        "network_required": False,
        "commands_are_not_executed": True,
        "runtime_changed_by_rf1_8": False,
        "dependency_versions_changed_by_rf1_8": False,
        "steps": [
            {
                "step_id": "verify_bundle_layout",
                "description": "Verify bundle layout and manifest before using the bundle.",
                "command": f"python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-bundle --repo-root . --bundle-dir {bundle_arg} --json",
            },
            {
                "step_id": "verify_artifact_presence",
                "description": "Verify that required artifact directories contain payloads.",
                "command": f"python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-artifacts --repo-root . --bundle-dir {bundle_arg} --json",
            },
            {
                "step_id": "verify_checksums",
                "description": "Verify checks/sha256sums.txt against bundle files.",
                "command": f"python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-checksums --repo-root . --bundle-dir {bundle_arg} --json",
            },
            {
                "step_id": "review_inventory",
                "description": "Review expected profile and operator bundle inventory summary.",
                "command": f"python3 scripts/kw_offline_bootstrap_bundle_tool.py inventory-summary --repo-root . --bundle-dir {bundle_arg} --json",
            },
            {
                "step_id": "load_docker_images_if_required",
                "description": "Operator loads prepared Docker image archives manually when the offline host lacks images.",
                "command": "for image_archive in offline_bootstrap/docker/images/*.tar; do docker load -i \"$image_archive\"; done",
            },
            {
                "step_id": "compose_check_only",
                "description": "Validate Compose/runtime packaging without starting services.",
                "command": "python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --check-only",
            },
            {
                "step_id": "runtime_smoke_skip_build",
                "description": "Run runtime smoke using already available Docker images.",
                "command": "python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --skip-build --timeout 1200",
            },
        ],
        "notes": [
            "This is a dry-run recipe only; RF1.8 does not execute these commands.",
            "Any online preparation must happen explicitly outside default offline runtime.",
            "Do not run npm audit fix --force without a separate controlled patch.",
        ],
        "expected_profile": expected_offline_profile(repo_root),
    }


def bundle_readiness_report(repo_root: Path, bundle_dir: Path) -> dict[str, Any]:
    layout_errors = validate_bundle_dir(bundle_dir)
    artifact_errors = validate_artifact_presence(bundle_dir)
    checksum_report = validate_checksums(bundle_dir)
    inventory = inventory_summary(repo_root, bundle_dir)

    sections = {
        "layout": {"status": "ready" if not layout_errors else "failed", "errors": layout_errors},
        "artifact_presence": {"status": "ready" if not artifact_errors else "failed", "errors": artifact_errors},
        "checksum_integrity": checksum_report,
        "inventory": inventory,
        "expected_profile": expected_offline_profile(repo_root),
        "dry_run_recipe": offline_build_recipe(repo_root, bundle_dir),
    }

    all_errors: list[str] = []
    for section_name in ("layout", "artifact_presence", "checksum_integrity", "inventory"):
        errors = sections[section_name].get("errors", [])
        all_errors.extend(f"{section_name}: {error}" for error in errors)

    return {
        "mode": "offline-bundle-readiness-report",
        "bundle_dir": str(bundle_dir),
        "network_required": False,
        "commands_executed": False,
        "runtime_changed_by_rf1_8": False,
        "dependency_versions_changed_by_rf1_8": False,
        "sections": sections,
        "errors": all_errors,
        "status": "ready" if not all_errors else "failed",
    }


def operator_command_groups(repo_root: Path) -> dict[str, Any]:
    return {
        "mode": "offline-operator-command-groups",
        "network_required_by_command_printer": False,
        "commands_are_not_executed": True,
        "runtime_changed_by_rf1_9": False,
        "dependency_versions_changed_by_rf1_9": False,
        "groups": {
            "policy_checks": [
                "python3 scripts/kw_offline_dependency_inventory_check.py --repo-root . --require-ready",
                "python3 scripts/kw_offline_bootstrap_bundle_check.py --repo-root . --require-ready",
                "python3 scripts/kw_offline_bootstrap_manifest_check.py --repo-root . --require-ready",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py check-policy --repo-root . --require-ready --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py check-artifact-policy --repo-root . --require-ready --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py check-integrity-policy --repo-root . --require-ready --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py check-inventory-policy --repo-root . --require-ready --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py check-readiness-policy --repo-root . --require-ready --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py check-closure-policy --repo-root . --require-ready --json",
            ],
            "template_and_layout": [
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py create-template --repo-root . --bundle-dir /path/to/offline_bootstrap",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-bundle --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
            ],
            "artifact_preparation_explicit_online_or_mirror": [
                "python3 -m pip download --requirement requirements.txt --dest /path/to/offline_bootstrap/python/wheelhouse",
                "cd frontend && npm ci --cache /path/to/offline_bootstrap/npm/cache --prefer-offline --no-audit --no-fund",
                "docker pull python:3.12-slim && docker save python:3.12-slim -o /path/to/offline_bootstrap/docker/images/python-3.12-slim.tar",
                "docker pull node:20-alpine && docker save node:20-alpine -o /path/to/offline_bootstrap/docker/images/node-20-alpine.tar",
                "docker pull postgres:16 && docker save postgres:16 -o /path/to/offline_bootstrap/docker/images/postgres-16.tar",
                "cd frontend && PLAYWRIGHT_BROWSERS_PATH=/path/to/offline_bootstrap/playwright/browsers npx playwright install chromium",
            ],
            "artifact_verification": [
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-artifacts --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
                "cd /path/to/offline_bootstrap && find . -type f ! -path './checks/sha256sums.txt' -print0 | sort -z | xargs -0 sha256sum > checks/sha256sums.txt",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-checksums --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py expected-profile --repo-root . --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py inventory-summary --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
                "python3 scripts/kw_offline_bootstrap_bundle_tool.py bundle-readiness-report --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
            ],
            "runtime_smoke": [
                "python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --check-only",
                "python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --skip-build --timeout 1200",
            ],
            "cleanup_and_hygiene": [
                "rm -f .env.deploy .npmrc .proxy.env .proxy.env.example",
                "git restore frontend/next-env.d.ts 2>/dev/null || true",
                "git status --short",
            ],
            "next_phase_options": [
                "RF2 slides runtime continuation and maximum product value",
                "controlled dependency/security step without npm audit fix --force",
                "docs-only branch/phase checkpoint before runtime work",
            ],
        },
        "notes": [
            "This command prints command groups only; it does not execute them.",
            "Commands in artifact_preparation_explicit_online_or_mirror are explicit operator actions and may require online or intranet mirror access.",
            "Do not run npm audit fix --force without a separate controlled patch.",
        ],
        "expected_profile": expected_offline_profile(repo_root),
    }


def rf1_closure_report(repo_root: Path) -> dict[str, Any]:
    groups = operator_command_groups(repo_root)
    return {
        "mode": "rf1-closure-report",
        "network_required": False,
        "commands_are_not_executed": True,
        "runtime_changed_by_rf1_9": False,
        "dependency_versions_changed_by_rf1_9": False,
        "branch": current_branch(repo_root),
        "commit": current_commit(repo_root),
        "rf1_checkpoints": list(RF1_CHECKPOINTS),
        "operator_command_group_count": len(groups["groups"]),
        "required_post_acceptance_checks": [
            "full KWS runner PASS",
            "Docker runtime smoke --skip-build PASS",
            "remote 7_Runtime_Foundation matches local RF1.9 verdict commit",
            "working tree clean after cleanup",
        ],
        "next_phase_options": groups["groups"]["next_phase_options"],
        "npm_audit_force_policy": "forbidden_without_separate_controlled_patch",
        "status": "ready",
    }


def validate_policy(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_POLICY_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing required RF1.9 policy surface: {rel}")

    tooling_doc = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_TOOLING.md"
    if tooling_doc.exists():
        doc = read_text(tooling_doc)
        for phrase in (
            "RF1.4 checkpoint",
            "check-policy",
            "create-template",
            "verify-bundle",
            "RF1.5 artifact presence checks",
            "verify-artifacts",
            "RF1.6 checksum and integrity verification",
            "verify-checksums",
            "RF1.7 artifact inventory summaries",
            "inventory-summary",
            "expected-profile",
            "RF1.8 bundle readiness report",
            "bundle-readiness-report",
            "offline-build-dry-run",
            "RF1.9 operator command groups",
            "operator-command-groups",
            "rf1-closure-report",
            "check-closure-policy",
        ):
            if phrase not in doc:
                errors.append(f"offline bootstrap bundle tooling doc is missing phrase: {phrase}")

    runbook = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md"
    if runbook.exists():
        doc = read_text(runbook)
        for phrase in (
            "RF1.5 checkpoint",
            "RF1.6 checksum verification commands",
            "RF1.7 artifact inventory commands",
            "RF1.8 bundle readiness report and dry-run commands",
            "RF1.9 operator command groups and closure commands",
            "operator-command-groups",
            "rf1-closure-report",
            "check-closure-policy",
            "does not change runtime behavior",
            "npm audit fix --force",
        ):
            if phrase not in doc:
                errors.append(f"offline bootstrap operator runbook is missing phrase: {phrase}")

    closure = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_RF1_CLOSURE.md"
    if closure.exists():
        doc = read_text(closure)
        for phrase in (
            "RF1.9 checkpoint",
            "operator-command-groups",
            "rf1-closure-report",
            "check-closure-policy",
            "RF1 closure criteria",
            "RF2",
            "controlled dependency/security step",
            "npm audit fix --force",
        ):
            if phrase not in doc:
                errors.append(f"RF1 closure doc is missing phrase: {phrase}")

    build_readiness = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_BUILD_READINESS.md"
    if build_readiness.exists():
        doc = read_text(build_readiness)
        for phrase in (
            "RF1.8 checkpoint",
            "bundle-readiness-report",
            "offline-build-dry-run",
            "commands_are_not_executed",
            "Production readiness gates must not require a real local `offline_bootstrap/` directory",
            "RF1.9 handoff",
        ):
            if phrase not in doc:
                errors.append(f"offline build readiness doc is missing phrase: {phrase}")

    gitignore = read_text(repo_root / ".gitignore") if (repo_root / ".gitignore").exists() else ""
    if "offline_bootstrap/" not in gitignore:
        errors.append(".gitignore must ignore offline_bootstrap/ operator bundles")

    if require_ready and (repo_root / "offline_bootstrap").exists():
        errors.append("operator offline_bootstrap/ must not be present at repo root during readiness")

    return errors


def runbook_commands() -> dict[str, list[str]]:
    groups = operator_command_groups(Path.cwd())["groups"]
    return {name: list(commands) for name, commands in groups.items()}


def create_template(repo_root: Path, bundle_dir: Path, force: bool, mode: str) -> dict[str, Any]:
    if mode not in ALLOWED_PREPARATION_MODES:
        raise ValueError("mode must be one of: " + ", ".join(sorted(ALLOWED_PREPARATION_MODES)))

    if bundle_dir.exists() and any(bundle_dir.iterdir()) and not force:
        raise FileExistsError(f"bundle directory is not empty; pass --force to overwrite template files: {bundle_dir}")

    for rel in (
        "python/wheelhouse",
        "npm/cache",
        "docker/images",
        "playwright/browsers",
        "checks",
    ):
        (bundle_dir / rel).mkdir(parents=True, exist_ok=True)

    write_text(
        bundle_dir / "README.md",
        "# KW Studio offline bootstrap bundle template\n\n"
        "This directory is an operator artifact generated by RF1 tooling.\n\n"
        "The template copies lock/source files and creates placeholder manifests. It does not contain real dependency artifacts until an operator explicitly prepares them.\n\n"
        "Do not commit this directory to git.\n",
    )
    copy_text_file(repo_root / "requirements.txt", bundle_dir / "python/requirements.txt")
    copy_text_file(repo_root / "frontend/package.json", bundle_dir / "npm/package.json")
    copy_text_file(repo_root / "frontend/package-lock.json", bundle_dir / "npm/package-lock.json")
    write_text(bundle_dir / "docker/images-manifest.txt", "\n".join(current_docker_images(repo_root)))
    write_text(bundle_dir / "playwright/browsers-manifest.txt", "operator-managed Playwright browser cache placeholder")
    write_text(bundle_dir / "checks/sha256sums.txt", "RF1.9 template placeholder; generate real checksums after artifact preparation")
    write_text(bundle_dir / "manifest.json", json.dumps(build_manifest_template(repo_root, mode), indent=2, sort_keys=True))

    errors = validate_bundle_dir(bundle_dir)
    return {
        "bundle_dir": str(bundle_dir),
        "created": True,
        "network_required": False,
        "downloads_performed": False,
        "package_managers_run": False,
        "docker_pull_or_save_run": False,
        "playwright_install_run": False,
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }


def command_check_policy(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors = validate_policy(repo_root, require_ready=args.require_ready)
    report = {
        "mode": "offline-bundle-tool-policy",
        "network_required": False,
        "runtime_changed_by_rf1_4": False,
        "dependency_versions_changed_by_rf1_4": False,
        "bundle_required": False,
        "commands": [
            "check-policy",
            "check-artifact-policy",
            "check-integrity-policy",
            "check-inventory-policy",
            "check-readiness-policy",
            "check-closure-policy",
            "expected-profile",
            "create-template",
            "verify-bundle",
            "verify-artifacts",
            "verify-checksums",
            "inventory-summary",
            "bundle-readiness-report",
            "offline-build-dry-run",
            "operator-command-groups",
            "rf1-closure-report",
            "print-runbook",
        ],
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_check_artifact_policy(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors = validate_policy(repo_root, require_ready=args.require_ready)
    report = {
        "mode": "offline-bundle-artifact-presence-policy",
        "network_required": False,
        "runtime_changed_by_rf1_5": False,
        "dependency_versions_changed_by_rf1_5": False,
        "bundle_required_for_readiness": False,
        "artifact_presence_requires_bundle_dir": True,
        "presence_rules": ARTIFACT_PRESENCE_RULES,
        "runbook_commands_documented": True,
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_check_integrity_policy(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors = validate_policy(repo_root, require_ready=args.require_ready)
    report = {
        "mode": "offline-bundle-checksum-integrity-policy",
        "network_required": False,
        "runtime_changed_by_rf1_6": False,
        "dependency_versions_changed_by_rf1_6": False,
        "bundle_required_for_readiness": False,
        "checksum_verification_requires_bundle_dir": True,
        "checksum_file": "checks/sha256sums.txt",
        "hash_algorithm": "sha256",
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_check_inventory_policy(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors = validate_policy(repo_root, require_ready=args.require_ready)
    profile = expected_offline_profile(repo_root)
    report = {
        "mode": "offline-artifact-inventory-policy",
        "network_required": False,
        "runtime_changed_by_rf1_7": False,
        "dependency_versions_changed_by_rf1_7": False,
        "bundle_required_for_readiness": False,
        "inventory_summary_requires_bundle_dir": True,
        "expected_profile_available": not errors,
        "expected_docker_images": profile["docker"]["expected_images"],
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_check_readiness_policy(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors = validate_policy(repo_root, require_ready=args.require_ready)
    recipe = offline_build_recipe(repo_root, None)
    report = {
        "mode": "offline-bundle-readiness-report-policy",
        "network_required": False,
        "runtime_changed_by_rf1_8": False,
        "dependency_versions_changed_by_rf1_8": False,
        "bundle_required_for_readiness": False,
        "bundle_readiness_report_requires_bundle_dir": True,
        "offline_build_dry_run_available": True,
        "dry_run_step_count": len(recipe["steps"]),
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_check_closure_policy(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    errors = validate_policy(repo_root, require_ready=args.require_ready)
    groups = operator_command_groups(repo_root)
    closure = rf1_closure_report(repo_root)
    required_groups = {
        "policy_checks",
        "template_and_layout",
        "artifact_preparation_explicit_online_or_mirror",
        "artifact_verification",
        "runtime_smoke",
        "cleanup_and_hygiene",
        "next_phase_options",
    }
    missing_groups = sorted(required_groups.difference(groups["groups"]))
    errors.extend(f"missing operator command group: {name}" for name in missing_groups)
    report = {
        "mode": "offline-rf1-closure-policy",
        "network_required": False,
        "runtime_changed_by_rf1_9": False,
        "dependency_versions_changed_by_rf1_9": False,
        "bundle_required_for_readiness": False,
        "commands_are_not_executed": True,
        "operator_command_group_count": len(groups["groups"]),
        "rf1_checkpoint_count": len(closure["rf1_checkpoints"]),
        "next_phase_options": closure["next_phase_options"],
        "npm_audit_force_policy": closure["npm_audit_force_policy"],
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_expected_profile(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = {
        "mode": "offline-expected-profile",
        "network_required": False,
        "profile": expected_offline_profile(repo_root),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def command_create_template(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    try:
        report = create_template(repo_root, bundle_dir, force=args.force, mode=args.mode)
    except Exception as exc:  # noqa: BLE001 - operator CLI should report all template creation issues.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["errors"] else 2


def command_verify_bundle(args: argparse.Namespace) -> int:
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    errors = validate_bundle_dir(bundle_dir)
    report = {
        "mode": "offline-bundle-verification",
        "bundle_dir": str(bundle_dir),
        "network_required": False,
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_verify_artifacts(args: argparse.Namespace) -> int:
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    errors = validate_artifact_presence(bundle_dir)
    report = {
        "mode": "offline-bundle-artifact-presence-verification",
        "bundle_dir": str(bundle_dir),
        "network_required": False,
        "downloads_performed": False,
        "package_managers_run": False,
        "docker_pull_or_save_run": False,
        "playwright_install_run": False,
        "presence_rules": ARTIFACT_PRESENCE_RULES,
        "errors": errors,
        "status": "ready" if not errors else "failed",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


def command_verify_checksums(args: argparse.Namespace) -> int:
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    validation = validate_checksums(bundle_dir)
    report = {
        "mode": "offline-bundle-checksum-verification",
        "bundle_dir": str(bundle_dir),
        "network_required": False,
        "downloads_performed": False,
        "package_managers_run": False,
        "docker_pull_or_save_run": False,
        "playwright_install_run": False,
        **validation,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["errors"] else 2


def command_inventory_summary(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    report = inventory_summary(repo_root, bundle_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["errors"] else 2


def command_bundle_readiness_report(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    report = bundle_readiness_report(repo_root, bundle_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["errors"] else 2


def command_offline_build_dry_run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    bundle_dir = Path(args.bundle_dir).expanduser().resolve() if args.bundle_dir else None
    report = offline_build_recipe(repo_root, bundle_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def command_operator_command_groups(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = operator_command_groups(repo_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def command_rf1_closure_report(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = rf1_closure_report(repo_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def command_print_runbook(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    report = {
        "mode": "offline-bootstrap-runbook-commands",
        "network_required_by_command_printer": False,
        "commands_are_not_executed": True,
        "commands_are_examples_only": True,
        "commands": operator_command_groups(repo_root)["groups"],
    }
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else json.dumps(report, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KW Studio offline bootstrap bundle template and verification tool.")
    sub = parser.add_subparsers(dest="command", required=True)

    policy = sub.add_parser("check-policy", help="Validate repository RF1 bundle tooling policy.")
    policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    policy.add_argument("--require-ready", action="store_true")
    policy.add_argument("--json", action="store_true")
    policy.set_defaults(func=command_check_policy)

    artifact_policy = sub.add_parser("check-artifact-policy", help="Validate RF1.5 artifact presence policy without requiring a bundle.")
    artifact_policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    artifact_policy.add_argument("--require-ready", action="store_true")
    artifact_policy.add_argument("--json", action="store_true")
    artifact_policy.set_defaults(func=command_check_artifact_policy)

    integrity_policy = sub.add_parser("check-integrity-policy", help="Validate RF1.6 checksum integrity policy without requiring a bundle.")
    integrity_policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    integrity_policy.add_argument("--require-ready", action="store_true")
    integrity_policy.add_argument("--json", action="store_true")
    integrity_policy.set_defaults(func=command_check_integrity_policy)

    inventory_policy = sub.add_parser("check-inventory-policy", help="Validate RF1.7 artifact inventory policy without requiring a bundle.")
    inventory_policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    inventory_policy.add_argument("--require-ready", action="store_true")
    inventory_policy.add_argument("--json", action="store_true")
    inventory_policy.set_defaults(func=command_check_inventory_policy)

    readiness_policy = sub.add_parser("check-readiness-policy", help="Validate RF1.8 bundle readiness report policy without requiring a bundle.")
    readiness_policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    readiness_policy.add_argument("--require-ready", action="store_true")
    readiness_policy.add_argument("--json", action="store_true")
    readiness_policy.set_defaults(func=command_check_readiness_policy)

    closure_policy = sub.add_parser("check-closure-policy", help="Validate RF1.9 closure policy without requiring a bundle.")
    closure_policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    closure_policy.add_argument("--require-ready", action="store_true")
    closure_policy.add_argument("--json", action="store_true")
    closure_policy.set_defaults(func=command_check_closure_policy)

    expected = sub.add_parser("expected-profile", help="Print expected offline profile derived from repository sources.")
    expected.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    expected.add_argument("--json", action="store_true")
    expected.set_defaults(func=command_expected_profile)

    create = sub.add_parser("create-template", help="Create an offline_bootstrap template directory without downloads.")
    create.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    create.add_argument("--bundle-dir", required=True)
    create.add_argument("--mode", default="online_bootstrap_preparation", choices=sorted(ALLOWED_PREPARATION_MODES))
    create.add_argument("--force", action="store_true")
    create.set_defaults(func=command_create_template)

    verify = sub.add_parser("verify-bundle", help="Verify an offline_bootstrap bundle layout and manifest.")
    verify.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    verify.add_argument("--bundle-dir", required=True)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=command_verify_bundle)

    verify_artifacts = sub.add_parser("verify-artifacts", help="Verify that a prepared offline_bootstrap bundle contains expected artifact payloads.")
    verify_artifacts.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    verify_artifacts.add_argument("--bundle-dir", required=True)
    verify_artifacts.add_argument("--json", action="store_true")
    verify_artifacts.set_defaults(func=command_verify_artifacts)

    verify_checksums = sub.add_parser("verify-checksums", help="Verify checks/sha256sums.txt against bundle files.")
    verify_checksums.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    verify_checksums.add_argument("--bundle-dir", required=True)
    verify_checksums.add_argument("--json", action="store_true")
    verify_checksums.set_defaults(func=command_verify_checksums)

    inventory = sub.add_parser("inventory-summary", help="Summarize an offline_bootstrap bundle and compare it to the expected profile.")
    inventory.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    inventory.add_argument("--bundle-dir", required=True)
    inventory.add_argument("--json", action="store_true")
    inventory.set_defaults(func=command_inventory_summary)

    readiness = sub.add_parser("bundle-readiness-report", help="Aggregate bundle layout, artifacts, checksums, inventory, and recipe status.")
    readiness.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    readiness.add_argument("--bundle-dir", required=True)
    readiness.add_argument("--json", action="store_true")
    readiness.set_defaults(func=command_bundle_readiness_report)

    dry_run = sub.add_parser("offline-build-dry-run", help="Print offline build/runtime recipe without executing commands.")
    dry_run.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    dry_run.add_argument("--bundle-dir", default=None)
    dry_run.add_argument("--json", action="store_true")
    dry_run.set_defaults(func=command_offline_build_dry_run)

    groups = sub.add_parser("operator-command-groups", help="Print grouped RF1 operator commands without executing them.")
    groups.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    groups.add_argument("--json", action="store_true")
    groups.set_defaults(func=command_operator_command_groups)

    closure = sub.add_parser("rf1-closure-report", help="Print RF1 closure summary and next phase options.")
    closure.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    closure.add_argument("--json", action="store_true")
    closure.set_defaults(func=command_rf1_closure_report)

    runbook = sub.add_parser("print-runbook", help="Print documented operator preparation commands as JSON.")
    runbook.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    runbook.add_argument("--json", action="store_true")
    runbook.set_defaults(func=command_print_runbook)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
