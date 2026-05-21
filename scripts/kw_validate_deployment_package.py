#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_FILES = (
    "Dockerfile.backend",
    "docker-compose.deploy.yml",
    ".env.deploy.example",
    ".dockerignore",
    "frontend/Dockerfile",
    "frontend/.dockerignore",
    "docs/deployment-packaging.md",
)

REQUIRED_BACKEND_SNIPPETS = (
    "FROM python:3.12-slim",
    "COPY backend ./backend",
    "COPY skills ./skills",
    "USER kwstudio",
    "HEALTHCHECK",
    "uvicorn",
    "backend.app.main:app",
)

REQUIRED_FRONTEND_SNIPPETS = (
    "FROM node:20-alpine",
    "npm run build",
    ".next/standalone",
    "USER nextjs",
    'CMD ["node", "server.js"]',
)

REQUIRED_COMPOSE_SNIPPETS = (
    "postgres:",
    "backend:",
    "frontend:",
    "DEPLOYMENT_MODE: ${DEPLOYMENT_MODE:-offline_intranet}",
    "DATABASE_URL: ${DATABASE_URL:?",
    "SECRET_KEY: ${SECRET_KEY:?",
    "STORAGE_ROOT: ${STORAGE_ROOT:-/app/storage}",
    "kw_storage:/app/storage",
    "condition: service_healthy",
)

FORBIDDEN_VALUES = (
    "sk-proj-",
    "Bearer ",
    "GIGACHAT_API_KEY=",
    "OPENAI_API_KEY=",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(repo_root: Path, path: str) -> str:
    return (repo_root / path).read_text(encoding="utf-8")


def require_file(repo_root: Path, path: str) -> list[str]:
    return [] if (repo_root / path).is_file() else [f"missing required packaging file: {path}"]


def require_snippets(label: str, content: str, snippets: tuple[str, ...]) -> list[str]:
    return [f"{label} missing required snippet: {snippet}" for snippet in snippets if snippet not in content]


def validate_package(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        errors.extend(require_file(repo_root, path))

    if errors:
        return errors

    backend_dockerfile = read_text(repo_root, "Dockerfile.backend")
    frontend_dockerfile = read_text(repo_root, "frontend/Dockerfile")
    compose = read_text(repo_root, "docker-compose.deploy.yml")
    next_config = read_text(repo_root, "frontend/next.config.mjs")
    requirements = read_text(repo_root, "requirements.txt")
    env_example = read_text(repo_root, ".env.deploy.example")

    errors.extend(require_snippets("Dockerfile.backend", backend_dockerfile, REQUIRED_BACKEND_SNIPPETS))
    errors.extend(require_snippets("frontend/Dockerfile", frontend_dockerfile, REQUIRED_FRONTEND_SNIPPETS))
    errors.extend(require_snippets("docker-compose.deploy.yml", compose, REQUIRED_COMPOSE_SNIPPETS))

    if 'output: "standalone"' not in next_config:
        errors.append('frontend/next.config.mjs must enable output: "standalone" for container runtime packaging.')

    if "psycopg[binary]" not in requirements:
        errors.append("requirements.txt must include psycopg[binary] for Postgres deployment packaging.")

    if "CHANGE_ME" not in env_example:
        errors.append(".env.deploy.example must use explicit CHANGE_ME placeholders.")

    if "DEPLOYMENT_MODE=offline_intranet" not in env_example:
        errors.append(".env.deploy.example must use the approved offline_intranet deployment mode.")

    if "LLM_PROVIDER=gigachat" not in env_example:
        errors.append(".env.deploy.example must document the approved gigachat readiness provider.")

    required_storage_env = (
        "STORAGE_ROOT=/app/storage",
        "UPLOADS_DIR=/app/storage/uploads",
        "ARTIFACTS_DIR=/app/storage/artifacts",
        "TEMP_DIR=/app/storage/temp",
    )
    if any(item not in env_example for item in required_storage_env):
        errors.append(".env.deploy.example must align local storage paths with the backend volume.")

    for forbidden in FORBIDDEN_VALUES:
        if forbidden in compose or forbidden in env_example:
            errors.append(f"deployment packaging must not contain real secret marker: {forbidden}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KW Studio deployment packaging files.")
    parser.add_argument("--repo-root", default=str(repo_root_from_script()), help="Repository root path.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    print(f"[INFO] repo_root={repo_root}")

    errors = validate_package(repo_root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 2

    print("[PASS] deployment packaging files are present and internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
