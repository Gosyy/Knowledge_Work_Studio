# KR-3E Active Gate Legacy Retirement

KR-3E removes active production-readiness-gate references to the first legacy
stage baseline-pinned checker batch recorded by KR-3C.

## Product reason

The production readiness gate should prove the current KW Studio product
contracts. It should not depend on historical stage checkers whose assertions
were written for earlier branch baselines, raw commit assumptions, or
stage-specific proof packs.

This is a product reset step, not a deletion step.

## What changes

The active `scripts/kw_production_readiness_gate.py` contract now runs
product/refactor replacement checks for:

```text
KR product reset roadmap
KR-3E active gate retirement
product workflow aliases
low-risk operator/static replacement coverage
slides product quality replacement coverage
DOCX/PDF/XLSX product workflow coverage
path portability policy
path portability cleanup plan
legacy baseline-pin retirement manifest
```

## What is retired from the active gate

The following legacy stage checkers are no longer required or executed by the
production readiness gate:

```text
scripts/kw_p9_1_human_review_results_check.py
scripts/kw_k0_kimi_rubric_check.py
scripts/kw_k2_plan_editor_check.py
scripts/kw_k3_renderer_quality_check.py
scripts/kw_k4_visual_qa_check.py
scripts/kw_k5_source_to_slide_provenance_check.py
scripts/kw_k6_end_to_end_workflow_check.py
scripts/kw_kq1_deck_quality_check.py
scripts/kw_p10_10_final_release_approval_dossier.py
scripts/kw_p10_11_final_operator_release_closure.py
scripts/kw_p10_1_post_p9_regeneration_readiness_check.py
scripts/kw_p10_2_post_p9_artifact_pack.py
scripts/kw_k_phase_release_readiness_check.py
```

## What does not change

legacy scripts are not deleted in KR-3E.

docs/codex is not moved or physically archived in KR-3E.

Legacy smoke tests and historical checkers may still exist as safety-net and
forensic material until later controlled archive/delete batches prove that the
corresponding product replacement coverage is accepted.

## Acceptance

KR-3E is accepted only when:

```text
kw_active_gate_legacy_retirement_check.py reports ready;
production readiness gate checks-only passes;
targeted KR-3E tests pass;
full runner passes from committed project scripts;
Docker smoke passes from committed project scripts;
logs are archived under the repository logs directory;
remote branch contains the accepted commit.
```
