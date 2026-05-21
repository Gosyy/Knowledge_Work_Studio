# S12 — Selected benchmark execution packet / human review workflow

S12 turns the S10 benchmark contract and S11 closure dossier into an execution-ready packet workflow. It does not execute the 12 scenarios, does not fill review results, and does not claim selected parity.

## Purpose

S12 prepares the operator workflow for running the selected Kimi Slides-class offline benchmark:

1. create a scenario execution manifest for all 12 S10 scenarios;
2. require an evidence manifest per scenario;
3. require one human review worksheet per scenario;
4. provide reviewer instructions and an ingest schema boundary;
5. preserve the S11 claim boundary until real completed review results exist.

## Required packet components

- `scenario_execution_manifest`
- `scenario_evidence_manifest`
- `human_review_worksheets`
- `reviewer_instructions`
- `review_result_ingest_schema`
- `operator_handoff_readme`

## Required per-scenario evidence

Each scenario must carry:

- approved plan snapshot;
- generated PPTX;
- artifact manifest;
- safe metadata;
- citation manifest;
- render geometry manifest;
- render-based visual QA report;
- human review worksheet.

## Human review worksheet state

All worksheets start as `pending_human_review`. S12 does not invent decisions. The only allowed future decisions are `approve`, `request_rework`, and `reject`.

The review worksheet must include reviewer identity, review timestamp, decision, score dimensions, slide-level findings, visual defects, citation findings, follow-up backlog, and a claim-safety acknowledgement.

## Claim boundary

S12 preserves the S10/S11 boundary:

- selected offline workflow parity is not supported now;
- future completed 12-scenario benchmark results are required;
- real completed human review is required;
- auto-approval is forbidden;
- `Kimi-level achieved` is forbidden;
- whole-project Kimi-level parity is forbidden.

The only allowed future claim wording remains:

```text
Kimi Slides-class offline workflow parity for selected benchmark scenarios.
```

## Offline boundary

S12 remains offline/intranet-safe. It does not add cloud research, cloud vision, hidden public internet, API endpoints, database migrations, dependency changes, Docker changes, or frontend runtime changes.

## Acceptance

S12 is accepted only when:

- `kw_s12_selected_benchmark_execution_packet_check.py --require-ready` passes;
- the S12 smoke test passes;
- production readiness includes the S12 checkpoint;
- full runner and Docker smoke pass after commit and push.
