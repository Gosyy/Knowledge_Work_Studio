# KW Studio RF1.10 Controlled Dependency and Security Baseline Assessment

## Status

RF1.10 checkpoint: controlled dependency/security baseline assessment without forced upgrades.

This checkpoint is assessment-only. It records the dependency/security review policy and adds a no-network report/checker for the current repository dependency surface. It does not change dependency versions, does not edit lockfiles, does not change Dockerfiles, does not change runtime behavior, and does not run `npm audit fix --force`.

## Why this exists

RF1 closed the offline/intranet operator foundation and RF2.0 started the slides runtime phase. Before deeper slides runtime work, the frontend and dependency warnings should be tracked separately from product-runtime changes.

The current full runners have consistently passed backend tests, frontend build, frontend E2E, production readiness, Docker check-only, and Docker runtime smoke. The npm warnings are therefore not release-blocking, but they should be assessed in a controlled way.

## Observed warning categories

The full-runner logs have shown:

- Node engine warning for a transitive frontend package on the operator host;
- deprecated npm packages in the frontend dependency tree;
- npm audit summary with vulnerabilities;
- recommendation from npm to run `npm audit fix --force`.

The last recommendation is explicitly not accepted as an automatic action.

## Policy

RF1.10 requires:

- no automatic dependency upgrades;
- no `npm audit fix --force`;
- no manual `package-lock.json` surgery;
- no mixing dependency/security remediation with RF2 slides runtime work;
- no network dependency in default production readiness gates;
- no change to Dockerfiles or runtime behavior;
- all future dependency remediation to be separate, narrow, reviewed patches.

## Assessment CLI

Default no-network policy assessment:

```bash
python3 scripts/kw_controlled_dependency_security_assessment.py \
  --repo-root . \
  --require-ready \
  --json
```

Optional local audit JSON analysis:

```bash
cd frontend
npm audit --json > ../logs/npm-audit-rf-sec0.json

cd ..
python3 scripts/kw_controlled_dependency_security_assessment.py \
  --repo-root . \
  --audit-json logs/npm-audit-rf-sec0.json \
  --json
```

The checker reads an audit JSON file only when the operator explicitly provides it. It does not run `npm audit` itself.

## Risk buckets

Findings must be classified into:

1. runtime-impacting;
2. dev-only/tooling;
3. transitive/no direct control;
4. requires major or breaking upgrade;
5. unknown until audit evidence is reviewed.

## Baseline surfaces

RF1.10 tracks these surfaces:

- `requirements.txt`;
- `frontend/package.json`;
- `frontend/package-lock.json`;
- `Dockerfile.backend`;
- `frontend/Dockerfile`;
- `docker-compose.deploy.yml`;
- Node/npm host observations reported by full-runner logs;
- Docker image baselines from RF1 offline inventory;
- existing RF1/RF2 readiness gates.

## Non-goals

RF1.10 must not:

- run `npm audit fix`;
- run `npm audit fix --force`;
- run dependency upgrades;
- change dependency versions;
- edit `frontend/package-lock.json`;
- edit `frontend/package.json`;
- edit `requirements.txt`;
- edit Dockerfiles;
- change Node version;
- change runtime behavior;
- change slides runtime implementation.

## Acceptance

RF1.10 is accepted when:

- this policy document exists;
- the checker reports `status: ready`;
- `npm_audit_fix_force_allowed` is `false`;
- `fixes_applied` is `false`;
- dependency/runtime change markers remain false;
- smoke tests cover policy mode and optional audit JSON summarization;
- production readiness includes the RF1.10 policy check;
- the post-RF1.10 full runner passes;
- Docker runtime smoke with `--skip-build` passes;
- remote `7_Runtime_Foundation` matches the local RF1.10 verdict commit;
- working tree is clean after cleanup.

## Handoff

After RF1.10 acceptance, continue with:

RF2.1 — Slides runtime capability inventory and baseline smoke.

If the audit report shows a high-confidence runtime-impacting issue, address it in a separate controlled remediation patch. Do not combine that with RF2 slides runtime work.
