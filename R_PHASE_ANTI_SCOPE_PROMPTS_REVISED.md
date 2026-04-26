# R Phase Anti-Scope Prompts — Revised

## Purpose

This file protects R phase from scope drift.

R phase is about full-stack deployment verification and operator-grade hardening. It is not a product expansion phase, not a rewrite phase, and not a new infrastructure phase.

---

# Universal anti-scope block for every R issue

```text
Work from the repository root.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state.
- Inspect live file contents before planning changes.
- Do not generate patches against stale snapshots.
- Prefer narrow additive changes over broad rewrites.
- Preserve all accepted O/P contracts.
- Preserve the final production readiness gate unless this issue explicitly modifies it.
- If a file has drifted, re-plan against live contents.
- If patch compatibility is uncertain, stop and report exact conflicting files.

File delivery rules:
- Provide changes through a repo-root Python apply script named apply_rX_<slug>.py.
- The script must validate repository root.
- The script must print [PASS] or [OK] for every changed file/block.
- The script must fail loudly on missing anchors.
- The script must not leave temporary files tracked.
- The script must not print secrets.
- The script must not require network access.

Hard anti-scope:
- Do NOT redesign the application architecture.
- Do NOT replace FastAPI, Next.js, Playwright, Docker Compose, SQLite, Postgres, or current repository abstractions.
- Do NOT add Kubernetes, Terraform, Helm, cloud deploy, TLS termination, or external object storage unless the issue explicitly says so.
- Do NOT add auth/product subscription systems.
- Do NOT remove or weaken tests to pass CI.
- Do NOT expose storage_key/storage_uri/local paths through public APIs.
- Do NOT print DATABASE_URL, SECRET_KEY, tokens, API keys, passwords, or DSN credentials.
- Do NOT commit .env.deploy or any real secret file.
- Do NOT perform broad dependency upgrades except in R8.
```

---

# R1 Anti-Scope — Full-stack Docker Compose smoke

```text
Implement R1 only.

Allowed:
- docker compose smoke script;
- --check-only / --dry-run behavior;
- optional CI workflow;
- docs;
- tests that mock subprocess behavior and do not require Docker.

Forbidden:
- no Kubernetes;
- no cloud deployment;
- no TLS/reverse proxy;
- no production secret manager;
- no replacing existing deployment packaging;
- no requiring Docker for normal unit tests.
```

---

# R2 Anti-Scope — Schema lifecycle preflight

```text
Implement R2 only.

Allowed:
- read-only schema checks;
- table/column inventory;
- safe status output;
- docs/tests.

Forbidden:
- no destructive migrations;
- no automatic production schema mutation;
- no DB schema redesign;
- no data backfill;
- no printing DSN credentials.
```

---

# R3 Anti-Scope — Artifact download UI

```text
Implement R3 only.

Allowed:
- frontend artifact client;
- artifact history panel;
- E2E smoke with mocked API;
- docs.

Forbidden:
- no artifact generation changes;
- no storage backend changes;
- no exposing storage_key/storage_uri;
- no bulk export;
- no signed URL system;
- no unrelated UI redesign.
```

---

# R4 Anti-Scope — Restore audit and confirmation UX

```text
Implement R4 only.

Allowed:
- restore audit metadata where existing boundaries allow;
- safer frontend confirmation UI;
- tests preserving non-destructive semantics;
- docs.

Forbidden:
- no destructive rollback;
- no deleting versions;
- no mutating historical versions;
- no branch/DAG editor;
- no collaborative conflict system;
- no auth redesign.
```

---

# R5 Anti-Scope — Operator runbook and backup/restore drill

```text
Implement R5 only.

Allowed:
- dry-run backup command generation;
- restore-check guidance;
- docs;
- tests for redaction and command generation.

Forbidden:
- no real destructive restore by default;
- no cloud backup;
- no S3/GCS;
- no cron scheduler;
- no external backup vendor;
- no secret printing.
```

---

# R6 Anti-Scope — Env and secret validation

```text
Implement R6 only.

Allowed:
- env file validation;
- placeholder detection;
- SECRET_KEY strength checks;
- DATABASE_URL safety classification;
- integration with preflight/final gate if narrow;
- docs/tests.

Forbidden:
- no secret manager integration;
- no Vault/KMS/1Password integration;
- no auth redesign;
- no storing secrets in repository;
- no printing secret values.
```

---

# R7 Anti-Scope — Observability baseline

```text
Implement R7 only.

Allowed:
- structured logging baseline;
- safe diagnostic CLI;
- health/ready detail improvements;
- tests/docs.

Forbidden:
- no Prometheus/Grafana stack;
- no OpenTelemetry collector;
- no external log shipping;
- no distributed tracing;
- no exposing secrets in diagnostics.
```

---

# R8 Anti-Scope — Dependency/security baseline

```text
Implement R8 only.

Allowed:
- narrow Next.js/security dependency update;
- package-lock update;
- build/E2E proof;
- docs;
- optional no-network audit wrapper.

Forbidden:
- no framework migration;
- no broad dependency churn;
- no React major upgrade unless explicitly required;
- no UI redesign;
- no backend dependency churn unrelated to security baseline.
```

---

# Codex-specific guardrails

## Production wording guard

```text
Do not infer extra infrastructure from the word production.
In this issue, production means verification/hardening within existing repository constraints.
Do not introduce new infrastructure layers unless explicitly listed in allowed scope.
```

## Patch guard

```text
Do not output a giant diff directly in chat.
Create a Python apply script that writes/patches exact files.
The apply script must be deterministic and fail on missing anchors.
```

## Test guard

```text
Do not delete or weaken existing tests.
If a test fails because the contract intentionally changed, update the legacy test to the new explicit contract and explain why.
Add focused regression tests for the new contract.
```

## Secret guard

```text
Never print secrets.
Never include real-looking tokens in tests.
Use placeholders that do not match real token prefixes.
If secret marker tests need marker literals, allowlist only scanner/test files that intentionally contain the catalog.
```

## Docker guard

```text
Do not make normal pytest require Docker.
Docker-dependent checks must be opt-in or CI-specific.
Scripts must have --check-only / --dry-run modes for local laptops without Docker.
```

---

# Final R phase review prompt

```text
Perform final R phase review as a whole branch.

Review:
- diff from origin/main;
- what entered in R1-R8;
- full-stack verification readiness;
- database/schema readiness;
- artifact/export UX;
- restore audit safety;
- env/secrets posture;
- observability posture;
- dependency/security posture;
- CI/workflow coverage;
- remaining risks;
- what to move to next phase;
- whether 6_Stage_R can be merged.

Separate hard blockers from acceptable next-phase risks.
```
