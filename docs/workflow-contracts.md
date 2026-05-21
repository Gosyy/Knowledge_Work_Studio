# S2 Workflow Contracts

S2 defines the first durable workflow contract registry for KW Studio. The goal is to make DOCX, PDF, slides, data/Python, browser-assisted, and LLM-provider workflows explicit before adding broader orchestration.

## Scope

S2 is intentionally a contract and validation step. It does not add a new queue, worker system, browser agent, OCR runtime, embedding service, or user-facing workflow builder.

## Mandatory workflow families

The registry in `backend/app/workflows/contracts.py` must contain exactly these workflow families:

- `docx` — DOCX transform workflow.
- `pdf` — PDF understanding workflow.
- `slides` — outline-first slide generation workflow.
- `data_python` — spreadsheet/CSV plus controlled Python analysis workflow.
- `browser_assisted` — internal-only browser-assisted workflow.
- `llm_provider` — offline LLM provider workflow that preserves local GigaChat as the default production provider.

## Shared contract rules

Each workflow contract records:

- lifecycle stages;
- accepted input kinds;
- output artifact kinds;
- required task/provenance events;
- approval gates;
- offline readiness;
- browser policy.

Every workflow must remain provenance-first and offline-ready. User files must produce registered artifacts with task history and source links. Generated content should never exist only as chat text when the workflow promises a downloadable work product.

## Kimi-derived slide workflow rule

Slides remain outline-first:

1. Create an outline/plan.
2. Let the user or operator inspect/edit the plan.
3. Select template/adaptive render mode.
4. Generate artifact.
5. Register artifact history and plan snapshot.
6. Allow retry from saved plan.

S2 only codifies this contract. It does not redesign the frontend slide UX.

## Browser-assisted workflow boundary

`browser_assisted` is internal-only in MVP. It is for controlled intranet/browser-assisted steps and evidence capture. It is not a full autonomous user-facing browser agent, and S2 does not introduce network dependencies.

## Validation

Run:

```bash
python scripts/kw_workflow_contracts_check.py --repo-root . --require-ready
python scripts/kw_workflow_contracts_check.py --repo-root . --workflow slides --json --require-ready
```

The production readiness gate runs the same registry check.
