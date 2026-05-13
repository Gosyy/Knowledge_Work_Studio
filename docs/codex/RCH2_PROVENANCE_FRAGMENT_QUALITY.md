# RCH2 — Provenance Fragment Quality and Diversity

Status: controlled release-candidate hardening checkpoint.

RCH2 improves the K5 source-to-slide provenance layer without adding a new public API, database migration, frontend runtime, dependency change, Docker change, cloud LLM, or cloud vision runtime.

## Goal

RCH2 turns K5 provenance from mechanically complete coverage into more reviewable evidence selection:

- deterministic slide-aware fragment selection;
- fragment diversity guard;
- evidence usefulness metadata;
- source diversity reporting;
- low-quality link detection for human review;
- stable safe metadata without raw source text.

## Scope

RCH2 changes only the local K-phase provenance runtime and related verification assets:

- `backend/app/services/k_phase/source_to_slide_provenance.py`
- `scripts/kw_rch2_provenance_fragment_quality_check.py`
- `backend/tests/smoke/test_rch2_provenance_fragment_quality.py`
- production readiness bookkeeping

## Non-goals

RCH2 does not claim that KW Studio is Kimi-level. RCH2 does not add a new endpoint, schema migration, dependency, Docker image, cloud model, or frontend runtime.

## Acceptance

RCH2 is accepted only when:

- every slide still has source-to-slide coverage;
- source fragments are selected by deterministic relevance/diversity scoring;
- safe metadata reports evidence quality status;
- raw source text is not stored in safe metadata;
- K5 and RCH2 checkers pass;
- production readiness gate passes;
- full runner and Docker smoke pass after commit.
