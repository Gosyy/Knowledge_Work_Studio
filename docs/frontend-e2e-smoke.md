# P2 Frontend E2E deck revision smoke

P2 adds a browser-level smoke test for the editable deck workflow.

## What it covers

The smoke test opens the Next.js app and verifies:

- the presentation registry panel renders;
- a session id can be entered;
- presentation metadata can be loaded from mocked backend responses;
- the plan snapshot inspector controls are visible;
- the current plan can be loaded;
- the revision form can create a slide revision;
- the revision POST body does **not** contain an explicit `plan` payload.

The test uses Playwright request interception for backend endpoints, so it does not require:

- a running backend;
- a real LLM;
- real PPTX generation;
- Postgres.

## Local setup

Install frontend dependencies:

```bash
cd frontend
npm install
```

Install the Chromium browser used by Playwright:

```bash
npx playwright install chromium
```

## Run

```bash
cd frontend
npm run test:e2e:smoke
```

The Playwright config starts the local Next.js dev server with:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Backend traffic is mocked inside the test via `page.route`.

## CI

The workflow is defined in:

```text
.github/workflows/frontend-e2e-smoke.yml
```

It runs:

```bash
npm ci --no-audit --no-fund --progress=false
npx playwright install --with-deps chromium
NEXT_TELEMETRY_DISABLED=1 npm run build
npm run test:e2e:smoke
```

## Scope boundaries

This is a smoke test. It intentionally does not test every visual detail and does not perform real backend mutation.
