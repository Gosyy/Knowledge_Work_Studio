# KW Studio Offline Build Readiness Report

## Status

RF1.8 checkpoint: offline build recipe dry-run and bundle readiness report.

This checkpoint adds a read-only readiness report for an operator-provided `offline_bootstrap/` bundle and a dry-run recipe for offline build/runtime preparation. It does not download dependencies, run package managers, pull Docker images, save Docker archives, install Playwright browsers, change dependency versions, change Docker build logic, or change runtime behavior.

## Purpose

RF1.1 through RF1.7 created the offline bootstrap chain:

- dependency inventory;
- bundle strategy;
- manifest validation;
- template and bundle verification;
- artifact presence checks;
- checksum/integrity verification;
- artifact inventory summaries and expected profile.

RF1.8 aggregates these checks into one operator-facing readiness report.

## CLI commands

Readiness policy check used by production gates:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py check-readiness-policy \
  --repo-root . \
  --require-ready \
  --json
```

Operator bundle readiness report:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py bundle-readiness-report \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

Offline build recipe dry-run:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py offline-build-dry-run \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

## Report sections

`bundle-readiness-report` includes:

- bundle layout status;
- artifact presence status;
- checksum integrity status;
- inventory status;
- expected offline profile;
- dry-run offline build/runtime recipe;
- final `ready` or `failed` status.

The command is read-only. It does not execute the recipe.

## Dry-run recipe

The dry-run recipe documents safe operator steps such as:

- verify bundle layout;
- verify artifact presence;
- verify checksums;
- review inventory summary;
- load Docker image archives manually if required;
- configure offline package indexes or caches;
- run Docker compose check-only;
- run runtime smoke with `--skip-build` when images already exist.

The recipe is a plan, not an executor.

The JSON dry-run report must expose `commands_are_not_executed: true` so automated checks and operators can verify that RF1.8 prints a recipe without executing it.

## Readiness behavior

Production readiness gates must not require a real local `offline_bootstrap/` directory.

Readiness only checks that:

- the RF1.8 policy document exists;
- `check-readiness-policy` is available;
- expected profile derivation works without network access;
- root-level operator bundles remain ignored by git.

## Non-goals

RF1.8 must not:

- run `pip download`;
- run `pip install`;
- run `npm ci`;
- run npm cache population;
- run `docker pull`;
- run `docker save`;
- install Playwright browsers;
- run offline build commands automatically;
- resolve npm audit findings;
- change dependency versions;
- change Dockerfiles;
- change runtime behavior.

## RF1.8 acceptance

RF1.8 is accepted when:

- this readiness policy document exists;
- `check-readiness-policy` passes;
- `bundle-readiness-report` is covered by smoke tests for ready and not-ready bundles;
- `offline-build-dry-run` is covered by smoke tests;
- production readiness includes the RF1.8 policy check;
- the full post-RF1.8 runner passes before the verdict commit is considered accepted.

## RF1.9 handoff

RF1.9 may add controlled offline build/run command documentation or split the RF1 chain into operator-facing command groups.

Any network use must remain explicit and outside default offline runtime.
