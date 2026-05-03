# KW Studio Offline Bootstrap Operator Runbook

## Status

RF1.5 checkpoint: offline bundle artifact presence checks and operator runbook commands.

This runbook documents explicit operator commands for preparing offline artifacts. RF1.5 does not execute those commands automatically.

## Purpose

RF1.1 identified dependency surfaces. RF1.2 defined the offline bootstrap bundle strategy. RF1.3 defined manifest validation. RF1.4 added template generation and bundle verification. RF1.5 adds artifact presence checks and documents explicit operator preparation commands.

## Operator modes

### Online bootstrap preparation

Use only on an approved connected workstation or connected intranet staging node.

Allowed actions in this mode:

- download Python wheels;
- prepare npm cache or local registry data;
- pull and save Docker images;
- install or export Playwright browser binaries;
- generate checksums.

This mode is not default production runtime.

### Offline transfer

Move the prepared bundle into the offline environment using the organization's approved media and integrity procedures.

### Offline verification

Run bundle verification in the offline environment before deployment.

### Offline runtime

Run KW Studio without package downloads, image pulls, browser downloads, or cloud services.

## Canonical bundle creation

Create a template first:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py create-template \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap
```

Verify the template layout:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-bundle \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

## Python wheelhouse preparation command

Example operator command for a connected preparation node:

```bash
python3 -m pip download \
  --requirement requirements.txt \
  --dest /path/to/offline_bootstrap/python/wheelhouse
```

Offline install must use the local wheelhouse or an internal package index only.

## npm cache preparation command

Example operator command for a connected preparation node:

```bash
cd frontend
npm ci \
  --cache /path/to/offline_bootstrap/npm/cache \
  --prefer-offline \
  --no-audit \
  --no-fund
```

Offline frontend build must use the prepared npm cache or an internal npm registry only.

## Docker image preparation commands

Example operator commands for a connected preparation node:

```bash
docker pull python:3.12-slim
docker pull node:20-alpine
docker pull postgres:16

docker save python:3.12-slim -o /path/to/offline_bootstrap/docker/images/python-3.12-slim.tar
docker save node:20-alpine -o /path/to/offline_bootstrap/docker/images/node-20-alpine.tar
docker save postgres:16 -o /path/to/offline_bootstrap/docker/images/postgres-16.tar
```

Record image names in:

```text
offline_bootstrap/docker/images-manifest.txt
```

Offline runtime smoke with `--skip-build` expects required images to already exist on the host.

## Playwright browser preparation command

Example operator command for a connected preparation node:

```bash
cd frontend
PLAYWRIGHT_BROWSERS_PATH=/path/to/offline_bootstrap/playwright/browsers \
  npx playwright install chromium
```

Offline E2E must use pre-provisioned browser binaries only.

## Checksum command

Example checksum inventory command:

```bash
cd /path/to/offline_bootstrap
find . -type f -print0 | sort -z | xargs -0 sha256sum > checks/sha256sums.txt
```

## Artifact presence verification

After the operator prepares artifacts, verify presence:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-artifacts \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

The presence check confirms that expected artifact directories and manifest files are non-empty. It does not replace cryptographic verification, vulnerability review, or organization-specific approval.

## Git hygiene

Do not commit:

- `offline_bootstrap/`
- wheelhouse files;
- npm cache files;
- Docker image archives;
- Playwright browser binaries;
- generated local checksums;
- `.env.deploy`, `.npmrc`, `.proxy.env`, `.proxy.env.example`.

## RF1.6 handoff

RF1.6 may add deeper offline artifact verification, such as checksum validation, expected Docker image digest checks, wheelhouse package enumeration, npm cache inventory checks, or documented offline build commands. Any network use must remain explicit and separate from default offline runtime.

## RF1.6 checksum verification commands

After preparing artifact payloads, generate checksums without including the checksum file itself:

```bash
cd /path/to/offline_bootstrap
find . -type f ! -path './checks/sha256sums.txt' -print0 \
  | sort -z \
  | xargs -0 sha256sum > checks/sha256sums.txt
```

Verify checksums in the offline environment:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-checksums \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

RF1.6 does not generate artifacts automatically and does not change runtime behavior.

## RF1.7 artifact inventory commands

Review the expected offline profile derived from repository files:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py expected-profile \
  --repo-root . \
  --json
```

Summarize an operator bundle:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py inventory-summary \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

RF1.7 inventory commands are read-only. They do not download dependencies, run package managers, pull Docker images, install browsers, or change runtime behavior.
