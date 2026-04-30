# Codex Operating Rules

## Absolute first step for every task

Before any patch, Codex must verify the previous accepted verdict.

For R-phase:

```bash
git fetch origin
git switch 6_Stage_R
git pull --ff-only
git log --oneline -8
git status --short
```

Codex must report:

```text
latest accepted verdict: <commit subject>
next allowed task: <R/S step>
blocked: yes/no
```

If the previous step is not accepted, Codex must stop.

## Patch delivery rule

Codex must not output giant diffs in chat.

Every implementation patch must be delivered as a repo-root Python apply script:

```text
apply_rX_<slug>.py
apply_sX_<slug>.py
```

The script must:
- validate repository root;
- validate expected files exist;
- inspect anchors before changing files;
- fail loudly on missing anchors;
- print `[PASS]` or `[OK]` for each changed file/block;
- be deterministic and idempotent where practical;
- not require network access;
- not print secrets;
- not leave temporary tracked files.

## Current-branch-state rule

Codex must work against live checked-out contents, not stale assumptions.

Required behavior:
- inspect current files before planning;
- if file contents drifted, re-plan;
- if patch compatibility is uncertain, stop and report exact conflicting files.

## Scope guard

Codex must not:
- redesign the application architecture;
- replace FastAPI, Next.js, Playwright, Docker Compose, SQLite, Postgres, or repository abstractions;
- add Kubernetes, Terraform, Helm, cloud deploy, TLS termination, external object storage, or secret-manager systems unless the current issue explicitly says so;
- add subscription/auth/RBAC systems;
- remove or weaken tests to pass CI;
- expose `storage_key`, `storage_uri`, or local paths through public APIs/UI;
- print `DATABASE_URL`, `SECRET_KEY`, tokens, API keys, passwords, DSN credentials, or real-looking secrets;
- commit `.env.deploy` or any real secret file;
- perform broad dependency upgrades outside R8.

## Docker guard

Normal pytest must not require Docker.

Docker-dependent checks must be opt-in, manual, CI-specific, or protected by
`--check-only` / `--dry-run`.

## Offline guard

The product must support full offline/intranet operation.

Codex must not introduce runtime dependence on:
- internet access;
- external cloud APIs;
- Docker Hub pulls during production runtime;
- PyPI/npm installs during production runtime;
- OpenAI, Hugging Face, public GigaChat cloud, or similar external endpoints.

Any endpoint in production/offline mode must be internal `ip:port` or explicitly allowlisted.

## Commit protocol

Every step has at least two commits:

```bash
git commit -m "R<N> add <feature>"
git commit --allow-empty -m "R<N> verdict: ACCEPT"
```

If fixes are required after the functional commit:

```bash
git commit -m "R<N> fix <specific issue>"
git commit --allow-empty -m "R<N> verdict: ACCEPT"
```

Codex must not begin the next step until the verdict commit is pushed.
