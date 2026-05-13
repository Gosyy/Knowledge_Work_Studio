# Acceptance Gates

## Step status vocabulary

Use only:
- `IN PROGRESS`
- `NEEDS_FIX`
- `BLOCKED`
- `ACCEPT`

Do not say a step is accepted until the verdict commit exists.

## Required evidence before verdict

Collect:
```text
git status --short
git log --oneline -5
focused tests output
full relevant gate output
```

## R-phase verdict format

```bash
git commit --allow-empty -m "R<N> verdict: ACCEPT"
git push origin 6_Stage_R
```

## S-phase verdict format

```bash
git commit --allow-empty -m "S<N> verdict: ACCEPT"
git push origin <s-branch>
```

## Backend gate

```bash
python3 -m pytest <focused tests> -q
python3 -m pytest -q
python3 -m compileall backend scripts
```

## Frontend gate

```bash
cd frontend
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e:smoke
cd ..
```

## Production readiness gate

```bash
python3 scripts/kw_production_readiness_gate.py --repo-root . --postgres-mode safety
```

## Docker compose smoke gate

Only when required:

```bash
python3 scripts/kw_fullstack_compose_smoke.py --repo-root . --timeout 600
```

Normal pytest must not require Docker.

## If a gate fails

Codex must:
1. keep current step as `NEEDS_FIX`;
2. identify exact failure;
3. propose a narrow fix patch script;
4. rerun focused tests;
5. rerun required gate;
6. only then proceed to verdict.
