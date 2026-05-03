# KW Studio Offline Bootstrap Bundle Strategy

## Status

RF1.2 checkpoint: offline bootstrap bundle policy and cache strategy.

This checkpoint does not change runtime behavior, dependency versions, Docker build logic, package manager configuration, CI workflows, or deployment topology. It defines the operator-facing bundle layout and validation policy that later RF1 steps can implement.

## Purpose

KW Studio must support offline and intranet deployment without hidden public internet requirements. RF1.1 identified the dependency surfaces. RF1.2 defines the bootstrap bundle strategy for preparing those surfaces before an operator enters an offline environment.

## Explicit modes

KW Studio must keep these modes separate:

### check-only

Used by readiness gates and CI-style static validation.

Rules:
- does not pull Docker images;
- does not install Python packages;
- does not run `npm ci`;
- does not download Playwright browsers;
- does not contact public package registries.

### skip-build runtime smoke

Used when Docker images are already present on the host.

Rules:
- may run `docker compose up`;
- must not build images;
- must not pull missing images implicitly;
- validates backend `/health`, backend `/ready`, frontend HTTP response, and operator smoke.

### online bootstrap preparation

Used on an explicitly approved connected machine or connected intranet staging node.

Rules:
- may download Python wheels;
- may prepare npm cache or local registry artifacts;
- may pull Docker base/service images;
- may prepare Playwright browser binaries;
- must produce portable artifacts for offline transfer;
- must not be confused with default production runtime.

### offline build

Used after bootstrap artifacts are transferred into the offline environment.

Rules:
- Python install uses a local wheelhouse or internal package index only;
- npm install uses a local npm cache or internal registry only;
- Docker base and service images are preloaded or available from an internal registry only;
- Playwright tests use pre-provisioned browser binaries only;
- no public internet is required.

### offline runtime

Used for normal production operation.

Rules:
- no package install;
- no image pull;
- no browser download;
- no cloud LLM, OCR, visual QA, package registry, or public web dependency;
- Direct local GigaChat remains the default production LLM path.

## Bundle layout

The canonical offline bootstrap bundle layout is:

```text
offline_bootstrap/
  README.md
  manifest.json
  python/
    requirements.txt
    wheelhouse/
  npm/
    package.json
    package-lock.json
    cache/
  docker/
    images/
    images-manifest.txt
  playwright/
    browsers/
    browsers-manifest.txt
  checks/
    sha256sums.txt
```

The bundle directory itself is an operator artifact and must not be committed to git.

## Manifest policy

`offline_bootstrap/manifest.json` should describe:

- bundle schema version;
- KW Studio commit SHA;
- preparation timestamp;
- preparation host type;
- Python version and wheelhouse source;
- npm version and cache or registry source;
- Docker image list and digests when available;
- Playwright browser cache version;
- SHA-256 checksums for portable artifacts;
- whether the bundle was prepared in online bootstrap or intranet mirror mode.

The manifest is not introduced as a committed file in RF1.2. It is a future operator artifact format.

## Python wheelhouse strategy

Source of truth:

- `requirements.txt`

Bootstrap preparation should produce:

- copied `requirements.txt`;
- wheel files for all backend direct and transitive dependencies;
- a checksum inventory.

Offline build should use only local wheelhouse or an internal package index. It must not silently fall back to public PyPI.

## Frontend npm cache strategy

Sources of truth:

- `frontend/package.json`
- `frontend/package-lock.json`

Bootstrap preparation should produce:

- copied `package.json`;
- copied `package-lock.json`;
- npm cache or local registry artifact sufficient for `npm ci`;
- clear record of Node and npm versions used.

Offline build should use only the prepared npm cache or internal registry. It must not silently fall back to the public npm registry.

## Docker image strategy

Sources of truth:

- `Dockerfile.backend`
- `frontend/Dockerfile`
- `docker-compose.deploy.yml`

Current required images include:

- `python:3.12-slim`
- `node:20-alpine`
- `postgres:16`

Bootstrap preparation should export or mirror required base and service images.

Offline runtime smoke with `--skip-build` should use pre-existing images. Offline build should use preloaded images or an internal registry only.

## Playwright browser strategy

Sources of truth:

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/playwright.config.ts`

Bootstrap preparation should prepare browser binaries for E2E smoke tests. Offline E2E should use the prepared browser cache and must not download browsers during test execution.

## Git hygiene policy

The following must not be committed:

- `offline_bootstrap/`
- Python wheelhouse artifacts;
- npm cache artifacts;
- Docker image archives;
- Playwright browser caches;
- generated checksums for local operator bundles;
- `.env.deploy`, `.npmrc`, `.proxy.env`, `.proxy.env.example`;
- logs and runtime storage.

## RF1.2 acceptance

RF1.2 is accepted when:

- this strategy document exists;
- the no-network bootstrap strategy check passes;
- the RF1.2 smoke test passes;
- the production readiness gate includes the RF1.2 check;
- the full post-RF1.2 runner passes before the verdict commit is considered accepted.

## RF1.3 handoff

RF1.2 intentionally stops at policy and validation. RF1.3 may implement operator tooling for:

- generating a dependency bundle manifest;
- verifying that an offline bundle contains all required sections;
- checking local wheelhouse/cache/image/browser availability without using the public internet;
- documenting exact operator commands for online bootstrap, offline transfer, offline build, and offline runtime smoke.
