# RCH4 Golden Benchmark Human Review Workflow

RCH4 is a controlled release-candidate hardening checkpoint after RC5. It defines a formal human-review workflow for the five golden benchmark cases without changing product runtime behavior.

## Purpose

Automated K/RC/RCH gates prove deterministic execution, metadata safety, provenance coverage, visual QA heuristics, and release-pack evidence. They do not prove that a generated deck is actually good enough for a human operator or executive reviewer.

RCH4 closes that process gap by generating a machine-readable worksheet and operator-readable review report for the RC1 golden benchmark cases.

## Review workflow

For each golden benchmark case, a reviewer should inspect:

- generated PPTX artifact;
- RC1 manifest and safe metadata;
- RC2 quality review report;
- RC3 fallback-vs-GigaChat comparison when available;
- RC4 artifact pack and RC5 final dossier context.

The reviewer records:

- overall decision: `approve`, `request_rework`, or `reject`;
- per-slide findings;
- storyline quality notes;
- source-faithfulness notes;
- visual hierarchy and density notes;
- table/chart quality notes;
- provenance usefulness notes;
- visual QA interpretation notes;
- recommended follow-up patch.

## Scope guard

RCH4 is documentation/checker/test/gate scope only. It does not add product runtime logic, public API endpoints, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or Kimi-level claims.

## Acceptance

RCH4 is accepted only when:

- `scripts/kw_rch4_golden_benchmark_human_review.py --require-ready --json` reports `ready`;
- RCH4 smoke test passes;
- production readiness gate includes RCH4;
- full runner passes;
- Docker smoke passes.
