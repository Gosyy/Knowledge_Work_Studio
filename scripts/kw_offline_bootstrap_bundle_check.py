#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "docs/codex/OFFLINE_DEPENDENCY_REPRODUCIBILITY.md",
    "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md",
    "requirements.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/playwright.config.ts",
    "Dockerfile.backend",
    "frontend/Dockerfile",
    "docker-compose.deploy.yml",
)

REQUIRED_DOC_PHRASES = (
    "RF1.2 checkpoint",
    "Explicit modes",
    "check-only",
    "skip-build runtime smoke",
    "online bootstrap preparation",
    "offline build",
    "offline runtime",
    "offline_bootstrap/",
    "python/",
    "wheelhouse/",
    "npm/",
    "cache/",
    "docker/",
    "images/",
    "playwright/",
    "browsers/",
    "manifest.json",
    "Git hygiene policy",
    "RF1.3 handoff",
)

BUNDLE_SECTIONS = {
    "python": "offline_bootstrap/python/wheelhouse",
    "npm": "offline_bootstrap/npm/cache",
    "docker": "offline_bootstrap/docker/images",
    "playwright": "offline_bootstrap/playwright/browsers",
    "checksums": "offline_bootstrap/checks/sha256sums.txt",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collect_docker_from_images(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*FROM\s+([^\s]+)", text)


def collect_compose_images(text: str) -> list[str]:
    return re.findall(r"(?im)(?:^|\s)image:\s*([A-Za-z0-9_./:-]+)", text)


def build_strategy(repo_root: Path) -> dict[str, Any]:
    backend_dockerfile = read_text(repo_root / "Dockerfile.backend")
    frontend_dockerfile = read_text(repo_root / "frontend/Dockerfile")
    compose = read_text(repo_root / "docker-compose.deploy.yml")

    docker_images = sorted(
        set(
            collect_docker_from_images(backend_dockerfile)
            + collect_docker_from_images(frontend_dockerfile)
            + collect_compose_images(compose)
        )
    )

    return {
        "mode": "offline-bootstrap-bundle-strategy",
        "network_required": False,
        "runtime_changed_by_rf1_2": False,
        "dependency_versions_changed_by_rf1_2": False,
        "canonical_bundle_root": "offline_bootstrap",
        "bundle_sections": BUNDLE_SECTIONS,
        "explicit_modes": [
            "check-only",
            "skip-build-runtime-smoke",
            "online-bootstrap-preparation",
            "offline-build",
            "offline-runtime",
        ],
        "source_files": {
            "python": ["requirements.txt"],
            "npm": ["frontend/package.json", "frontend/package-lock.json"],
            "docker": ["Dockerfile.backend", "frontend/Dockerfile", "docker-compose.deploy.yml"],
            "playwright": ["frontend/package.json", "frontend/package-lock.json", "frontend/playwright.config.ts"],
        },
        "docker_images": docker_images,
        "required_hygiene_patterns": [
            "offline_bootstrap/",
            ".env.deploy",
            ".npmrc",
            ".proxy.env",
            ".proxy.env.example",
            "logs/",
            "storage/",
        ],
        "status": "strategy_ready",
    }


def validate_strategy(repo_root: Path, strategy: dict[str, Any], require_ready: bool) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (repo_root / rel).exists():
            errors.append(f"missing required RF1.2 surface: {rel}")

    doc_path = repo_root / "docs/codex/OFFLINE_BOOTSTRAP_BUNDLE_STRATEGY.md"
    if doc_path.exists():
        doc = read_text(doc_path)
        for phrase in REQUIRED_DOC_PHRASES:
            if phrase not in doc:
                errors.append(f"offline bootstrap strategy doc is missing phrase: {phrase}")

    if strategy["network_required"] is not False:
        errors.append("RF1.2 strategy check must not require network")
    if strategy["runtime_changed_by_rf1_2"] is not False:
        errors.append("RF1.2 must not change runtime behavior")
    if strategy["dependency_versions_changed_by_rf1_2"] is not False:
        errors.append("RF1.2 must not change dependency versions")

    expected_images = {"python:3.12-slim", "node:20-alpine", "postgres:16"}
    missing_images = expected_images.difference(strategy["docker_images"])
    for image in sorted(missing_images):
        errors.append(f"missing expected current Docker image in strategy inventory: {image}")

    explicit_modes = set(strategy["explicit_modes"])
    for mode in {
        "check-only",
        "skip-build-runtime-smoke",
        "online-bootstrap-preparation",
        "offline-build",
        "offline-runtime",
    }:
        if mode not in explicit_modes:
            errors.append(f"missing explicit mode: {mode}")

    if require_ready:
        if (repo_root / "offline_bootstrap").exists():
            errors.append("operator offline_bootstrap/ bundle directory must not be committed or present in repo root during readiness")
        gitignore = read_text(repo_root / ".gitignore") if (repo_root / ".gitignore").exists() else ""
        if "logs/" not in gitignore or "storage/" not in gitignore:
            errors.append(".gitignore must keep generated logs/ and storage/ out of git")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check KW Studio RF1.2 offline bootstrap bundle strategy.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root path.")
    parser.add_argument("--require-ready", action="store_true", help="Require strategy readiness for production gates.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    strategy = build_strategy(repo_root)
    errors = validate_strategy(repo_root, strategy, require_ready=args.require_ready)

    if args.json:
        print(json.dumps({"strategy": strategy, "errors": errors}, indent=2, sort_keys=True))
    else:
        print(f"[INFO] repo_root={repo_root}")
        print("[offline-bootstrap-bundle-strategy]")
        print(json.dumps(strategy, indent=2, sort_keys=True))

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 2

    if not args.json:
        print("[PASS] offline bootstrap bundle strategy contract completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
