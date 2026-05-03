# KW Studio Offline Dependency Reproducibility Policy

## Status

RF1.1 checkpoint: inventory and policy only.

This document defines the first Runtime Foundation dependency baseline after RF0. It does not change runtime behavior, dependency versions, Docker build logic, package managers, or deployment topology.

## Purpose

KW Studio must be deployable and testable in offline or intranet environments without hidden package registry, image registry, browser download, cloud API, or public internet assumptions.

RF1.1 records the dependency surfaces that must be made reproducible before later RF1 steps harden package caches, image caches, and deployment bundles.

## Current dependency surfaces

### Python backend

Source of truth:

- `requirements.txt`

Current direct requirements include:

- `fastapi`
- `uvicorn[standard]`
- `pydantic-settings`
- `httpx`
- `pytest`
- `python-multipart`
- `alembic`
- `boto3`
- `psycopg[binary]`

RF1.1 observation:

- Python requirements are range-based, not a fully locked wheelhouse manifest.
- This is acceptable for RF1.1 inventory.
- A later RF1 step must define an offline wheelhouse or equivalent locked artifact bundle.

### Frontend npm

Sources of truth:

- `frontend/package.json`
- `frontend/package-lock.json`

Current direct runtime dependencies:

- `next`
- `react`
- `react-dom`

Current direct development/build dependencies:

- `@types/node`
- `@types/react`
- `@types/react-dom`
- `eslint`
- `eslint-config-next`
- `typescript`
- `@playwright/test`

RF1.1 observation:

- `package-lock.json` exists and is the current npm reproducibility anchor.
- `npm ci` is still registry/cache-sensitive unless an offline npm cache or local registry is prepared.
- npm warnings and audit findings are RF1 follow-up inputs, not RF1.1 blockers.

### Docker images and build-time dependencies

Sources of truth:

- `Dockerfile.backend`
- `frontend/Dockerfile`
- `docker-compose.deploy.yml`

Current image/build dependency surfaces:

- backend image base: `python:3.12-slim`
- frontend image base: `node:20-alpine`
- Compose service image: `postgres:16`
- backend build runs `python -m pip install -r requirements.txt`
- frontend build runs `npm ci --no-audit --no-fund --progress=false`

RF1.1 observation:

- Docker check-only and skip-build runtime smoke are already useful for offline validation when images exist.
- A full Docker build still requires preloaded base images and available Python/npm dependency artifacts.
- A later RF1 step must define how these images and package artifacts are mirrored, exported, imported, or cached.

### Browser and E2E dependencies

Sources of truth:

- `frontend/playwright.config.ts`
- `frontend/package.json`
- `frontend/package-lock.json`

RF1.1 observation:

- Playwright test execution depends on browser binaries being available in the environment.
- A later RF1 step must document browser binary provisioning for offline test runners.

### Optional heavy runtime dependencies

Potential future surfaces:

- OCR
- embeddings
- rerank
- visual QA runtime
- LiteLLM gateway runtime
- local fallback model runtime

RF1.1 policy:

- These are optional Server 2 surfaces.
- They must remain opt-in.
- They must not become hidden dependencies of the default Server 1 plus Server 3 production path.

## Offline reproducibility policy

RF1 and later implementation work must preserve these rules:

1. No hidden internet requirement in default production runtime.
2. No package install from public registries during offline deploy unless the operator explicitly chooses an online/bootstrap mode.
3. No Docker image pull requirement during offline smoke unless the operator explicitly chooses a build/pull mode.
4. No Playwright browser download during offline test execution unless the operator explicitly chooses a browser-install/bootstrap mode.
5. No cloud LLM, cloud OCR, cloud visual QA, or public web dependency in default production workflows.
6. Direct local GigaChat remains the default production LLM path.
7. LiteLLM remains optional and must not silently replace direct local GigaChat.
8. Generated caches, wheelhouses, npm caches, Docker archives, Playwright browser caches, logs, and env/proxy files must not be committed to git.

## RF1 follow-up backlog

RF1.1 intentionally stops at inventory and policy. Later RF1 tasks should decide and implement:

- Python wheelhouse or equivalent locked package artifact strategy.
- npm cache or local registry strategy.
- Docker base image export/import or internal registry strategy.
- Playwright browser binary cache strategy.
- Offline bootstrap runbook.
- CI/operator checks that distinguish check-only, skip-build smoke, offline build, and online bootstrap modes.
- A clear response to npm engine warnings and audit findings observed in post-RF0 full-runner logs.

## RF1.1 acceptance

RF1.1 is accepted when:

- the inventory policy document exists;
- the no-network inventory check passes;
- the smoke test for the inventory check passes;
- the production readiness gate includes the inventory check;
- the full post-RF1.1 runner passes before the verdict commit is considered accepted.
