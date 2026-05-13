# KW Studio Offline Bootstrap Artifact Inventory

## Status

RF1.7 checkpoint: offline artifact inventory summaries and expected image/package listing.

This checkpoint adds read-only inventory summaries for operator-provided `offline_bootstrap/` bundles and an expected offline profile derived from repository source files. It does not download dependencies, run package managers, pull Docker images, save Docker archives, install Playwright browsers, change dependency versions, change Docker build logic, or change runtime behavior.

## Purpose

RF1.6 verifies that bundle files match `checks/sha256sums.txt`. RF1.7 adds operator-readable inventory summaries so a human can review what is present in the bundle and compare it to the expected KW Studio offline profile.

## Expected profile

The expected profile is derived from current repository files:

- `requirements.txt`;
- `frontend/package.json`;
- `frontend/package-lock.json`;
- `Dockerfile.backend`;
- `frontend/Dockerfile`;
- `docker-compose.deploy.yml`;
- `frontend/playwright.config.ts`.

The current required Docker images are expected to include:

- `python:3.12-slim`;
- `node:20-alpine`;
- `postgres:16`.

## CLI commands

Readiness policy check:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py check-inventory-policy \
  --repo-root . \
  --require-ready \
  --json
```

Expected offline profile:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py expected-profile \
  --repo-root . \
  --json
```

Operator bundle inventory summary:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py inventory-summary \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

## Inventory summary

`inventory-summary` reports:

- Python wheelhouse file count and bytes;
- npm cache file count and bytes;
- Docker image archive file count and bytes;
- Docker `images-manifest.txt` entries;
- missing expected Docker image manifest entries;
- Playwright browser cache file count and bytes;
- Playwright browser manifest entries;
- checksum entry count;
- copied source lockfile presence;
- expected profile information.

It does not prove that caches are complete, secure, or sufficient for every platform. It is a review and validation layer, not a package resolver.

## Readiness behavior

Production readiness gates must not require a real local `offline_bootstrap/` directory.

Readiness only checks that:

- artifact inventory policy is documented;
- CLI policy check is available;
- expected profile can be derived without network access;
- root-level operator bundles remain ignored by git.

## Non-goals

RF1.7 must not:

- run `pip download`;
- run `pip install`;
- run `npm ci`;
- run npm cache population;
- run `docker pull`;
- run `docker save`;
- install Playwright browsers;
- resolve npm audit findings;
- change dependency versions;
- change Dockerfiles;
- change runtime behavior.

## RF1.7 acceptance

RF1.7 is accepted when:

- this inventory policy document exists;
- `check-inventory-policy` passes;
- `expected-profile` is covered by smoke tests;
- `inventory-summary` is covered by smoke tests for template, populated, and missing-expected-image scenarios;
- production readiness includes the RF1.7 policy check;
- the full post-RF1.7 runner passes before the verdict commit is considered accepted.

## RF1.8 handoff

RF1.8 may add deeper offline build/runbook checks, such as checking that an operator bundle has enough data to execute an offline build recipe, or documenting controlled offline build commands.

Any network use must remain explicit and outside default offline runtime.
