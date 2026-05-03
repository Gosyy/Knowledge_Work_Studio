# KW Studio Offline Bootstrap Manifest and Bundle Validation

## Status

RF1.3 checkpoint: manifest schema and bundle validation tooling.

This checkpoint does not download dependencies, generate wheelhouses, populate npm caches, save Docker image archives, install Playwright browsers, change Dockerfiles, or change package versions. It does not change runtime behavior.

## Purpose

RF1.2 defined the offline bootstrap bundle strategy. RF1.3 defines the portable manifest schema and a validator that can check either:

- the repository-level manifest policy without requiring an actual bundle; or
- an operator-provided `offline_bootstrap/` bundle directory.

This creates the bridge between policy-only RF1.2 and future RF1 implementation work that may generate or verify real offline artifacts.

## Default readiness behavior

Production readiness gates must not require an actual local `offline_bootstrap/` directory.

By default, the RF1.3 validator checks:

- this manifest policy document exists;
- RF1.1 dependency inventory policy exists;
- RF1.2 bootstrap bundle strategy exists;
- source files for Python, npm, Docker, Compose, and Playwright are present;
- the expected manifest schema is internally complete;
- no committed operator bundle is required.

## Operator bundle validation behavior

When an operator provides `--bundle-dir`, the validator checks the supplied directory.

Expected layout:

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

## Manifest schema

`manifest.json` should contain:

```json
{
  "schema_version": "1",
  "kw_studio": {
    "commit": "<git commit sha>",
    "branch": "7_Runtime_Foundation"
  },
  "prepared": {
    "mode": "online_bootstrap_preparation",
    "timestamp_utc": "<ISO-8601 timestamp>",
    "host": "<operator host summary>"
  },
  "python": {
    "requirements_file": "python/requirements.txt",
    "wheelhouse_dir": "python/wheelhouse"
  },
  "npm": {
    "package_json": "npm/package.json",
    "package_lock": "npm/package-lock.json",
    "cache_dir": "npm/cache"
  },
  "docker": {
    "images_dir": "docker/images",
    "images_manifest": "docker/images-manifest.txt"
  },
  "playwright": {
    "browsers_dir": "playwright/browsers",
    "browsers_manifest": "playwright/browsers-manifest.txt"
  },
  "checks": {
    "sha256sums": "checks/sha256sums.txt"
  }
}
```

## Allowed preparation modes

The manifest `prepared.mode` should be one of:

- `online_bootstrap_preparation`
- `intranet_mirror_preparation`

The manifest must not describe normal offline runtime as a preparation mode.

## Git hygiene policy

The following remain operator artifacts and must not be committed:

- `offline_bootstrap/`
- wheelhouse files;
- npm cache files;
- Docker image archives;
- Playwright browser binaries;
- generated local checksums;
- local `.npmrc` or proxy/env files.

## RF1.3 acceptance

RF1.3 is accepted when:

- this manifest policy document exists;
- the no-network manifest schema check passes without requiring a bundle;
- the optional bundle validator path is covered by smoke tests using a temporary fixture;
- production readiness includes the RF1.3 manifest check;
- the full post-RF1.3 runner passes before the verdict commit is considered accepted.

## RF1.4 handoff

RF1.4 may implement operator tooling for preparing or verifying real offline artifacts, such as:

- generating an empty manifest template;
- copying source lockfiles into a bundle;
- verifying local wheelhouse/cache/image/browser availability;
- producing checksum inventories;
- documenting exact online bootstrap and offline transfer commands.

RF1.4 must still avoid hidden public internet use in default production runtime.

## RF1.4 bundle tooling

RF1.4 adds `scripts/kw_offline_bootstrap_bundle_tool.py`.

The tool can create a template bundle and verify bundle layout/manifest structure. It does not download dependencies, run package managers, pull Docker images, install browsers, or change runtime behavior.
