# KW Studio Offline Bootstrap Integrity Verification

## Status

RF1.6 checkpoint: offline checksum and artifact integrity verification.

This checkpoint adds checksum policy and verification for operator-provided `offline_bootstrap/` bundles. It does not download dependencies, run package managers, pull Docker images, save Docker archives, install Playwright browsers, change dependency versions, change Docker build logic, or change runtime behavior.

## Purpose

RF1.5 added artifact presence checks. Presence is not enough for offline transfer: operators also need deterministic integrity verification after moving a bundle into an offline environment.

RF1.6 adds `verify-checksums` support around `checks/sha256sums.txt`.

## Checksum file

The canonical checksum file is:

```text
offline_bootstrap/checks/sha256sums.txt
```

The expected format is compatible with `sha256sum` output:

```text
<64 hex chars>  <relative path>
```

Examples:

```text
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  python/wheelhouse/example.whl
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb  docker/images/postgres-16.tar
```

Paths must be relative to the bundle root. Absolute paths and parent traversal are rejected.

## CLI commands

Policy check used by readiness gates:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py check-integrity-policy \
  --repo-root . \
  --require-ready \
  --json
```

Operator checksum verification:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py verify-checksums \
  --repo-root . \
  --bundle-dir /path/to/offline_bootstrap \
  --json
```

## Operator checksum generation

Example operator command after artifact preparation:

```bash
cd /path/to/offline_bootstrap
find . -type f ! -path './checks/sha256sums.txt' -print0 \
  | sort -z \
  | xargs -0 sha256sum > checks/sha256sums.txt
```

The exclusion avoids hashing the checksum file while it is being generated.

## Readiness behavior

Production readiness gates must not require a real local `offline_bootstrap/` directory.

Readiness only checks that:

- checksum policy is documented;
- checksum CLI is available;
- `check-integrity-policy` passes;
- root-level operator bundles remain ignored by git.

## Non-goals

RF1.6 must not:

- generate real wheelhouses;
- download npm cache artifacts;
- pull or save Docker images;
- install Playwright browsers;
- verify vulnerability status;
- prove package completeness;
- change dependency versions;
- change Dockerfiles;
- change runtime behavior.

## RF1.6 acceptance

RF1.6 is accepted when:

- this integrity policy document exists;
- `check-integrity-policy` passes;
- `verify-checksums` is covered by smoke tests for valid and corrupted bundles;
- production readiness includes the RF1.6 policy check;
- the full post-RF1.6 runner passes before the verdict commit is considered accepted.

## RF1.7 handoff

RF1.7 may add deeper artifact inventory checks, such as expected wheel filename enumeration, npm cache inventory summaries, Docker image digest checks, or offline build command documentation.

Any network use must remain explicit and outside default offline runtime.
