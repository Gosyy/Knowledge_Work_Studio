# KW Studio Offline Bootstrap Bundle Tooling

## Status

RF1.4 checkpoint: offline bundle verification CLI and template generation.

This checkpoint adds operator tooling for creating a template `offline_bootstrap/` directory and verifying a bundle layout. It does not download dependencies, run package managers, pull Docker images, save Docker archives, install Playwright browsers, change dependency versions, change Docker build logic, or change runtime behavior.

## Purpose

RF1.1 identified dependency surfaces. RF1.2 defined the bootstrap bundle strategy. RF1.3 defined the manifest schema and validation rules. RF1.4 adds a small no-network CLI that operators can use before real offline artifacts exist.

## CLI commands

The canonical CLI is:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py <command> --repo-root .
```

### check-policy

Validates repository policy and readiness wiring.

Rules:
- no network;
- no bundle required;
- confirms RF1.1/RF1.2/RF1.3 documents exist;
- confirms `.gitignore` excludes `offline_bootstrap/`;
- confirms template generation remains an explicit operator action.

### create-template

Creates a skeleton bundle under an operator-specified directory:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py create-template \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap
```

The command may copy source lockfiles and generate a manifest template. It must not download or populate real dependency artifacts.

### verify-bundle

Verifies the bundle layout and manifest:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-bundle \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap
```

Verification checks structure and manifest consistency. It does not prove that wheelhouse/npm/Docker/browser caches are complete; future RF steps may add deeper artifact verification.

## Generated template layout

The template uses the RF1.2 layout:

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

## Git hygiene

`offline_bootstrap/` is an operator artifact and must not be committed.

RF1.4 updates repository hygiene so the default root-level `offline_bootstrap/` path is ignored by git.

## Non-goals

RF1.4 must not:

- run `pip download`;
- run `pip install`;
- run `npm ci`;
- run `npm cache`;
- run `docker pull`;
- run `docker save`;
- install Playwright browsers;
- change dependency versions;
- change Dockerfiles;
- change runtime behavior;
- commit generated operator bundles.

## RF1.4 acceptance

RF1.4 is accepted when:

- this tooling document exists;
- the CLI policy check passes;
- template generation into a temporary directory is covered by smoke tests;
- bundle verification of that temporary template is covered by smoke tests;
- production readiness includes the RF1.4 policy check;
- the full post-RF1.4 runner passes before the verdict commit is considered accepted.

## RF1.5 handoff

RF1.5 may add deeper artifact presence checks or documented operator commands for preparing wheelhouses, npm cache artifacts, Docker image archives, and Playwright browser caches. Any network-using preparation must remain explicit and separate from default offline runtime.
