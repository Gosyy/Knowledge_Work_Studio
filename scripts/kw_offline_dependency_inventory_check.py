#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "requirements.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
    "frontend/playwright.config.ts",
    "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md",
)

EXPECTED_FRONTEND_DEPS = ("next", "react", "react-dom")
EXPECTED_FRONTEND_DEV_DEPS = ("@playwright/test", "typescript", "eslint", "eslint-config-next")
EXPECTED_PYTHON_DIRECT_NAMES = (
    "fastapi",
    "uvicorn",
    "pydantic-settings",
    "httpx",
    "pytest",
    "python-multipart",
    "alembic",
    "boto3",
    "psycopg",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_requirement_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        tokens.extend(part.strip() for part in line.split() if part.strip())
    return tokens


def normalize_requirement_name(requirement: str) -> str:
    name = re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip()
    return name.lower().replace("_", "-")


def collect_docker_from_images(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*FROM\s+([^\s]+)", text)


def collect_compose_images(text: str) -> list[str]:
    return re.findall(r"(?im)(?:^|\s)image:\s*([A-Za-z0-9_./:-]+)", text)


def build_inventory(repo_root: Path) -> dict[str, Any]:
    requirements_path = repo_root / "requirements.txt"
    package_json_path = repo_root / "frontend/package.json"
    package_lock_path = repo_root / "frontend/package-lock.json"
    backend_dockerfile_path = repo_root / "Dockerfile.backend"
    frontend_dockerfile_path = repo_root / "frontend/Dockerfile"
    compose_path = repo_root / "docker-compose.deploy.yml"

    requirements_text = _read_text(requirements_path)
    python_requirements = parse_requirement_tokens(requirements_text)

    package_json = json.loads(_read_text(package_json_path))
    package_lock = json.loads(_read_text(package_lock_path))

    backend_dockerfile = _read_text(backend_dockerfile_path)
    frontend_dockerfile = _read_text(frontend_dockerfile_path)
    compose_text = _read_text(compose_path)

    lock_packages = package_lock.get("packages", {})
    if isinstance(lock_packages, dict):
        package_lock_package_count = len(lock_packages)
    else:
        package_lock_package_count = 0

    followups: list[str] = []
    if any((">=" in item or "<" in item or "~=" in item or "*" in item) for item in python_requirements):
        followups.append("python_requirements_are_range_based_define_wheelhouse_or_lock_strategy")
    if "npm ci" in frontend_dockerfile:
        followups.append("frontend_docker_build_requires_prepared_npm_cache_or_registry_for_offline_build")
    if "pip install -r requirements.txt" in backend_dockerfile:
        followups.append("backend_docker_build_requires_prepared_python_wheelhouse_or_index_for_offline_build")
    if "postgres:16" in compose_text:
        followups.append("postgres_image_must_be_preloaded_or_available_from_internal_registry")

    inventory: dict[str, Any] = {
        "mode": "offline-no-network-inventory",
        "network_required": False,
        "runtime_changed_by_rf1_1": False,
        "python": {
            "source": "requirements.txt",
            "direct_requirement_count": len(python_requirements),
            "direct_requirements": python_requirements,
            "normalized_direct_names": sorted({normalize_requirement_name(item) for item in python_requirements}),
        },
        "frontend": {
            "package": package_json.get("name"),
            "source": "frontend/package.json",
            "lock_source": "frontend/package-lock.json",
            "lockfile_version": package_lock.get("lockfileVersion"),
            "lock_package_count": package_lock_package_count,
            "dependencies": package_json.get("dependencies", {}),
            "dev_dependencies": package_json.get("devDependencies", {}),
            "scripts": package_json.get("scripts", {}),
        },
        "docker": {
            "backend_dockerfile": "Dockerfile.backend",
            "backend_from_images": collect_docker_from_images(backend_dockerfile),
            "backend_uses_requirements_install": "pip install -r requirements.txt" in backend_dockerfile,
            "frontend_dockerfile": "frontend/Dockerfile",
            "frontend_from_images": collect_docker_from_images(frontend_dockerfile),
            "frontend_uses_npm_ci": "npm ci" in frontend_dockerfile,
            "compose_file": "docker-compose.deploy.yml",
            "compose_images": collect_compose_images(compose_text),
            "compose_uses_backend_build": "backend:" in compose_text and "dockerfile: Dockerfile.backend" in compose_text,
            "compose_uses_frontend_build": "frontend:" in compose_text and "dockerfile: Dockerfile" in compose_text,
        },
        "browser_e2e": {
            "source": "frontend/playwright.config.ts",
            "playwright_declared": "@playwright/test" in package_json.get("devDependencies", {}),
            "offline_binary_cache_required_for_airgapped_tests": True,
        },
        "policy": {
            "default_runtime_must_not_require_internet": True,
            "online_bootstrap_must_be_explicit": True,
            "dependency_artifacts_must_not_be_committed": True,
            "direct_local_gigachat_remains_default": True,
            "litellm_remains_optional": True,
        },
        "followups": followups,
        "status": "ready_with_followups" if followups else "ready",
    }
    return inventory


def validate_inventory(repo_root: Path, inventory: dict[str, Any], require_ready: bool = False) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing required dependency inventory surface: {rel}")

    doc_path = repo_root / "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md"
    if doc_path.exists():
        doc = _read_text(doc_path)
        for phrase in (
            "RF1.1 checkpoint",
            "Offline reproducibility policy",
            "Python backend",
            "Frontend npm",
            "Docker images and build-time dependencies",
            "Browser and E2E dependencies",
        ):
            if phrase not in doc:
                errors.append(f"offline dependency policy doc is missing phrase: {phrase}")

    py_names = set(inventory["python"]["normalized_direct_names"])
    for expected in EXPECTED_PYTHON_DIRECT_NAMES:
        if expected not in py_names:
            errors.append(f"requirements.txt is missing expected direct dependency name: {expected}")

    frontend = inventory["frontend"]
    deps = frontend["dependencies"]
    dev_deps = frontend["dev_dependencies"]
    for dep in EXPECTED_FRONTEND_DEPS:
        if dep not in deps:
            errors.append(f"frontend/package.json is missing dependency: {dep}")
    for dep in EXPECTED_FRONTEND_DEV_DEPS:
        if dep not in dev_deps:
            errors.append(f"frontend/package.json is missing devDependency: {dep}")

    if frontend["lockfile_version"] is None:
        errors.append("frontend/package-lock.json does not expose lockfileVersion")
    if int(frontend["lock_package_count"] or 0) <= 0:
        errors.append("frontend/package-lock.json package inventory is empty")

    docker = inventory["docker"]
    if "python:3.12-slim" not in docker["backend_from_images"]:
        errors.append("Dockerfile.backend must declare python:3.12-slim as the current backend base image")
    if "node:20-alpine" not in docker["frontend_from_images"]:
        errors.append("frontend/Dockerfile must declare node:20-alpine as the current frontend base image")
    if "postgres:16" not in docker["compose_images"]:
        errors.append("docker-compose.deploy.yml must declare postgres:16 as the current Postgres service image")
    if require_ready and not inventory["browser_e2e"]["playwright_declared"]:
        errors.append("frontend package must declare @playwright/test for E2E smoke readiness")

    if inventory["network_required"] is not False:
        errors.append("RF1.1 inventory check must be no-network by default")
    if inventory["runtime_changed_by_rf1_1"] is not False:
        errors.append("RF1.1 must not change runtime behavior")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KW Studio offline dependency inventory and reproducibility policy.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root path.")
    parser.add_argument("--require-ready", action="store_true", help="Require the RF1.1 inventory to be ready for readiness gates.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    inventory = build_inventory(repo_root)
    errors = validate_inventory(repo_root, inventory, require_ready=args.require_ready)

    if args.json:
        print(json.dumps({"inventory": inventory, "errors": errors}, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[offline-dependency-inventory]")
        print(json.dumps(inventory, indent=2, sort_keys=True))
        for followup in inventory.get("followups", []):
            print(f"[FOLLOWUP] {followup}")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 2

    if not args.json:
        print("[PASS] offline dependency inventory contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
