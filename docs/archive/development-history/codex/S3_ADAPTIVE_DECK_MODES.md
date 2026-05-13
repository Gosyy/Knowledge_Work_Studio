# S3 — Adaptive deck modes

- status: `controlled_adaptive_deck_modes`
- branch: `9_Product_Release_Hardening`
- baseline before S3: `fb5d888f9348c07a57b94387f0b201f38c785010`
- Kimi-level claimed: `False`

## Purpose

S3 turns the S2 outline-first frontend workflow into a mode-aware deck planning contract. The goal is to avoid generic bullet decks by selecting a deck mode before generation and requiring mode-specific storyline stages, slide archetypes, table/chart policy, visual QA expectations, provenance expectations, and failure guards.

This is not a full renderer rewrite. It is the adaptive planning registry needed before S4 native table/chart/diagram rendering and S9 render-based visual QA.

## Adaptive deck modes

S3 defines five benchmark-aligned adaptive deck modes:

1. `executive_board_deck` — memo or brief to executive decision deck.
2. `architecture_review_deck` — technical architecture document to architecture review deck.
3. `project_status_deck` — project log to status review deck.
4. `decision_matrix_deck` — comparison table to decision matrix deck.
5. `long_document_explainer` — long DOCX/PDF to structured explainer.

Each mode defines:

- source intent;
- storyline stages;
- required slide archetypes;
- table/chart policy;
- visual QA expectations;
- provenance expectations;
- failure guards for known P9/P10 quality issues.

## Boundaries

S3 does not add public API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, browser runtime, or public-internet production dependency.

S3 does not claim Kimi-level parity and does not verify Server 3 `local_intranet` GigaChat. It prepares Kimi Slides-class workflow quality under offline/intranet constraints.

## Acceptance

S3 is accepted when:

- `scripts/kw_s3_adaptive_deck_modes_check.py --repo-root . --require-ready --json` reports `ready`;
- five adaptive deck modes are present;
- every mode has a mode-specific storyline and slide archetypes;
- table/chart policy is ready for S4;
- visual QA expectations are ready for S9;
- targeted pytest passes;
- production readiness `--checks-only` includes S3;
- after commit and push, full runner and Docker smoke pass.
