# KW Studio RF1 Offline Operator Command Groups and Closure Checkpoint

## Status

RF1.9 checkpoint: offline operator command groups and RF1 closure checkpoint.

This checkpoint closes the RF1 offline bootstrap foundation by grouping the operator-facing commands produced across RF1.1 through RF1.8 and by documenting the next safe transition choices. It does not download dependencies, run package managers, pull Docker images, save Docker archives, install Playwright browsers, change dependency versions, change Docker build logic, change runtime behavior, or run `npm audit fix --force`.

## RF1 scope recap

RF1 established the offline/intranet bootstrap foundation:

- RF1.1 — dependency inventory and reproducibility policy;
- RF1.2 — offline bootstrap bundle strategy;
- RF1.3 — manifest schema and validation;
- RF1.4 — template generation and bundle verification CLI;
- RF1.5 — artifact presence checks and operator runbook commands;
- RF1.6 — checksum and artifact integrity verification;
- RF1.7 — artifact inventory summaries and expected profile;
- RF1.8 — build recipe dry-run and bundle readiness report;
- RF1.9 — operator command groups and RF1 closure checkpoint.

## CLI commands

Production readiness policy check:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py check-closure-policy \
  --repo-root . \
  --require-ready \
  --json
```

Operator command groups:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py operator-command-groups \
  --repo-root . \
  --json
```

RF1 closure report:

```bash
python3 scripts/kw_offline_bootstrap_bundle_tool.py rf1-closure-report \
  --repo-root . \
  --json
```

## Operator command groups

RF1 command groups are read-only metadata unless the operator explicitly runs the printed shell commands.

The canonical groups are:

1. `policy_checks` — no bundle required, no network required.
2. `template_and_layout` — create and verify an operator bundle template.
3. `artifact_preparation_explicit_online_or_mirror` — explicit online or intranet mirror preparation commands.
4. `artifact_verification` — verify presence, checksums, inventory, and readiness report.
5. `runtime_smoke` — Docker compose check-only and `--skip-build` runtime smoke when images already exist.
6. `cleanup_and_hygiene` — remove generated local env/proxy files and restore frontend generated files.
7. `next_phase_options` — RF2 slides runtime or a separate controlled dependency/security step.

## RF1 closure criteria

RF1 is considered closed when:

- `check-closure-policy` passes;
- all RF1 policy commands from RF1.1 through RF1.9 are available;
- production readiness includes the RF1.9 closure policy check;
- the post-RF1.9 full runner passes;
- Docker runtime smoke with `--skip-build` passes;
- remote `7_Runtime_Foundation` matches the local RF1.9 verdict commit;
- working tree is clean after cleanup.

## Next phase options

After RF1.9 acceptance, do not silently start RF2.

Choose one of:

- RF2 — Slides runtime continuation and maximum product value;
- controlled dependency/security step — analyze Node/npm warnings and vulnerabilities without `npm audit fix --force`;
- branch/phase checkpoint — create a new branch or docs-only planning checkpoint before runtime work.

## Non-goals

RF1.9 must not:

- run `pip download`;
- run `pip install`;
- run `npm ci`;
- run npm cache population;
- run `docker pull`;
- run `docker save`;
- install Playwright browsers;
- run offline build commands automatically;
- resolve npm audit findings;
- run `npm audit fix --force`;
- change dependency versions;
- change Dockerfiles;
- change runtime behavior.

## Handoff

RF1.9 is the final RF1 closure checkpoint unless a narrow repair is required by logs.

After acceptance, continue only after the user chooses the next scope.
