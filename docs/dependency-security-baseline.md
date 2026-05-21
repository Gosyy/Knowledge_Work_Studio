# Dependency security baseline

R8 establishes a narrow dependency/security baseline for the frontend after the P and R operator hardening work.

## Decision

The frontend stays on the existing Next.js 14 major line and upgrades only the Next.js patch pair:

- `next`: `14.2.5` -> `14.2.35`
- `eslint-config-next`: `14.2.5` -> `14.2.35`

React, TypeScript, Playwright, ESLint, and type packages stay pinned at the existing versions.

This is intentionally not a framework migration. The R phase must avoid broad dependency churn, React major changes, App Router redesign, or UI rewrites.

## Why 14.2.35

Next.js published a December 2025 security update instructing applications on Next.js 14.x to move to the patched `14.2.x` line, with `14.2.35` listed as the fixed version for the affected 14.x release line.

Using `14.2.35` keeps KW Studio on the same major version while aligning the v14 baseline with the patched release line. Major upgrades to Next.js 15 or 16 belong to a later, separately scoped task with migration notes and expanded browser testing.

## Policy

1. Frontend runtime dependencies must be exact versions, not ranges.
2. R-phase dependency work must stay patch-level unless a dedicated migration task is approved.
3. `package-lock.json` must be committed with `package.json` changes.
4. The offline dependency audit must not invoke `npm audit`, registry lookups, or network calls.
5. Production readiness remains the final gate; dependency audit is an additional focused check.
6. Real secret values must never be committed in package metadata or lockfiles.

## Approved R8 baseline

```text
next=14.2.35
eslint-config-next=14.2.35
react=18.3.1
react-dom=18.3.1
@playwright/test=1.48.2
typescript=5.5.4
eslint=8.57.0
```

## Operator commands

After applying the R8 patch, update the lockfile from the repository root:

```bash
cd frontend
npm install --no-audit --no-fund --progress=false
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e:smoke
cd ..
```

Then run the offline dependency audit:

```bash
python3 scripts/kw_dependency_audit.py --repo-root .
python3 -m pytest backend/tests/smoke/test_r8_dependency_audit.py -q
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## Non-goals

R8 does not add:

- Next.js 15/16 migration;
- React major upgrade;
- npm registry security scanning in offline mode;
- SCA SaaS integration;
- Renovate/Dependabot policy;
- UI redesign.
