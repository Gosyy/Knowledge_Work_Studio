#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
        "rf1_4": {
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


def validate_policy(repo_root: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_POLICY_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing required RF1.5 policy surface: {rel}")

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
            "print-runbook",
            "RF1.5 handoff",
        ):
            if phrase not in doc and phrase != "RF1.5 handoff":
                errors.append(f"RF1.4/RF1.5 tooling doc is missing phrase: {phrase}")

    runbook = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_OPERATOR_RUNBOOK.md"
    if runbook.exists():
        doc = read_text(runbook)
        for phrase in (
            "RF1.5 checkpoint",
            "Python wheelhouse preparation command",
            "npm cache preparation command",
            "Docker image preparation commands",
            "Playwright browser preparation command",
            "Artifact presence verification",
            "RF1.6 handoff",
        ):
            if phrase not in doc:
                errors.append(f"RF1.5 operator runbook is missing phrase: {phrase}")

    gitignore = read_text(repo_root / ".gitignore") if (repo_root / ".gitignore").exists() else ""
    if "offline_bootstrap/" not in gitignore:
        errors.append(".gitignore must ignore offline_bootstrap/ operator bundles")

    if require_ready and (repo_root / "offline_bootstrap").exists():
        errors.append("operator offline_bootstrap/ must not be present at repo root during readiness")

    return errors


def runbook_commands() -> dict[str, list[str]]:
    return {
        "template": [
            "python3 scripts/kw_offline_bootstrap_bundle_tool.py create-template --repo-root . --bundle-dir /path/to/offline_bootstrap",
            "python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-bundle --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
        ],
        "python": [
            "python3 -m pip download --requirement requirements.txt --dest /path/to/offline_bootstrap/python/wheelhouse",
        ],
        "npm": [
            "cd frontend && npm ci --cache /path/to/offline_bootstrap/npm/cache --prefer-offline --no-audit --no-fund",
        ],
        "docker": [
            "docker pull python:3.12-slim",
            "docker pull node:20-alpine",
            "docker pull postgres:16",
            "docker save python:3.12-slim -o /path/to/offline_bootstrap/docker/images/python-3.12-slim.tar",
            "docker save node:20-alpine -o /path/to/offline_bootstrap/docker/images/node-20-alpine.tar",
            "docker save postgres:16 -o /path/to/offline_bootstrap/docker/images/postgres-16.tar",
        ],
        "playwright": [
            "cd frontend && PLAYWRIGHT_BROWSERS_PATH=/path/to/offline_bootstrap/playwright/browsers npx playwright install chromium",
        ],
        "checksums": [
            "cd /path/to/offline_bootstrap && find . -type f -print0 | sort -z | xargs -0 sha256sum > checks/sha256sums.txt",
        ],
        "verify_artifacts": [
            "python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-artifacts --repo-root . --bundle-dir /path/to/offline_bootstrap --json",
        ],
    }


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
        "This directory is an operator artifact generated by RF1.4/RF1.5 tooling.\n\n"
        "The template copies lock/source files and creates placeholder manifests. It does not contain real dependency artifacts until an operator explicitly prepares them.\n\n"
        "Do not commit this directory to git.\n",
    )
    copy_text_file(repo_root / "requirements.txt", bundle_dir / "python/requirements.txt")
    copy_text_file(repo_root / "frontend/package.json", bundle_dir / "npm/package.json")
    copy_text_file(repo_root / "frontend/package-lock.json", bundle_dir / "npm/package-lock.json")
    write_text(bundle_dir / "docker/images-manifest.txt", "\n".join(current_docker_images(repo_root)))
    write_text(bundle_dir / "playwright/browsers-manifest.txt", "operator-managed Playwright browser cache placeholder")
    write_text(bundle_dir / "checks/sha256sums.txt", "RF1.4 template placeholder; generate real checksums in a later operator step")
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
        "commands": ["check-policy", "check-artifact-policy", "create-template", "verify-bundle", "verify-artifacts", "print-runbook"],
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


def command_print_runbook(args: argparse.Namespace) -> int:
    report = {
        "mode": "offline-bootstrap-runbook-commands",
        "network_required_by_command_printer": False,
        "commands_are_examples_only": True,
        "commands": runbook_commands(),
    }
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else json.dumps(report, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KW Studio offline bootstrap bundle template and verification tool.")
    sub = parser.add_subparsers(dest="command", required=True)

    policy = sub.add_parser("check-policy", help="Validate repository RF1.4/RF1.5 bundle tooling policy.")
    policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    policy.add_argument("--require-ready", action="store_true")
    policy.add_argument("--json", action="store_true")
    policy.set_defaults(func=command_check_policy)

    artifact_policy = sub.add_parser("check-artifact-policy", help="Validate RF1.5 artifact presence policy without requiring a bundle.")
    artifact_policy.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    artifact_policy.add_argument("--require-ready", action="store_true")
    artifact_policy.add_argument("--json", action="store_true")
    artifact_policy.set_defaults(func=command_check_artifact_policy)

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
