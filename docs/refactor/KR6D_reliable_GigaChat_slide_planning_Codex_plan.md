# KR-6D reliable GigaChat slide planning contract — Codex plan

This task-specific plan must be used together with:

```text
docs/refactor/CODEX_PROJECT_BRIEFING.md
docs/refactor/PROJECT_MIGRATION_HANDOFF.md
README.md
AGENTS.md
```

Codex must read the project briefing before working on this plan. The briefing defines project-wide rules, protected contracts and acceptance process. This document defines the KR-6D task.

## Current blocker

Public internet GigaChat runtime mode works and `/execute` can call GigaChat and download a PPTX artifact. However, real user slide planning falls back because the LLM plan is rejected as:

```text
llm_plan_invalid
```

The system currently lacks actionable sanitized validation diagnostics and repair retry. The fallback deck is better than earlier placeholder output, but it is not reliable real LLM planning and still may leak template UI labels into public PPTX text.

KR-6D must introduce a reliable slide planning contract, not merely adjust prompt wording.

## Global preamble for every Codex step

Before editing code for any step, Codex must:

```text
1. Read CODEX_PROJECT_BRIEFING.md.
2. Read PROJECT_MIGRATION_HANDOFF.md.
3. Inspect current git branch, HEAD, origin HEAD and dirty tree.
4. Inspect local .env.deploy presence without printing secrets.
5. Inspect relevant source files and tests before patching.
6. Avoid weakening runtime/offline guardrails.
7. Preserve KR-6C source-mode routing and RF2/RF2.1 media baseline.
8. Update PROJECT_MIGRATION_HANDOFF.md when behavior or procedure changes.
9. Run targeted checks and git diff --check.
10. Do not claim ACCEPT without full runner, Docker smoke, push and remote verification.
```

## A. Preflight and local-state audit

### Goal

Build a reliable preflight/audit layer for the KR-6D patch so work starts from actual local state and actual evidence.

### Acceptance criteria

The runner or documented procedure must record:

```text
branch
local HEAD
remote HEAD
dirty tree
untracked files
.env.deploy presence without secret values
Docker Compose projects
containers and ports
kw-studio volumes
latest slides_result.json if available
latest backend-tail.log if available
latest PPTX evidence if available
```

The patch must not proceed over unknown dirty state. Expected partial states must be explicitly classified.

### Codex prompt

```text
You are working on KR-6D for KW Studio. Before code changes, implement or update the apply runner so it records actual local repository and runtime state. Read docs/refactor/CODEX_PROJECT_BRIEFING.md and PROJECT_MIGRATION_HANDOFF.md. Do not assume a clean checkout. Do not print .env.deploy secrets. If dirty state exists, classify it and fail unless it is an explicitly expected continuation state. Preserve profile neutrality.
```

### Negative prompt

```text
Do not pull over unknown dirty state. Do not delete local env files or Docker volumes in preflight. Do not print secrets. Do not treat absence of .env.deploy as an error unless the specific deploy step requires it.
```

## B. Versioned LLM JSON contract

### Goal

Replace loose dictionary expectations with an explicit, versioned slide-plan contract.

### Required schema

```json
{
  "schema_version": "slides_plan.v1",
  "deck_title": "string",
  "audience": "string",
  "tone": "string",
  "slides": [
    {
      "slide_number": 1,
      "title": "string",
      "slide_type": "title|section|content|comparison|timeline|conclusion",
      "bullets": ["string", "string"],
      "speaker_notes": "string"
    }
  ]
}
```

### Acceptance criteria

```text
schema_version is required and equals slides_plan.v1.
slides length equals requested_slide_count.
slide_number is exactly 1..N.
title is non-empty, unique, business-readable and not a prompt echo.
slide_type is from an allowlist.
bullets length is 2..5.
each bullet is meaningful, not a UI template label and not generic filler.
speaker_notes is optional for rendering but must be validated if present.
unknown extra fields are either rejected or ignored with a warning; behavior must be documented.
```

### Codex prompt

```text
Implement a versioned LLM slide plan contract for KR-6D. Prefer a small typed validation layer near backend/app/services/slides_service/user_prompt_planning.py or a dedicated module if cleaner. Preserve existing public API compatibility unless tests require explicit metadata additions. Do not break legacy/source-aware planning. Add tests for valid schema, missing schema_version, wrong slide count, invalid slide_type, duplicate slide numbers, prompt echo and template-label leakage.
```

### Negative prompt

```text
Do not accept any dict with a slides key as valid. Do not silently coerce wrong slide counts. Do not let Additional insight, Local deterministic slide image generation, Key points, Option A / Current path or Step 1 pass validation as public text.
```

## C. Robust parser

### Goal

Make LLM response parsing robust and diagnosable.

### Acceptance criteria

Parser accepts:

```text
plain JSON
fenced ```json JSON
JSON with short text before or after
BOM and whitespace
valid JSON with newline-containing bullet strings
```

Parser rejects with typed error codes:

```text
no_json_object
json_decode_error
top_level_not_object
multiple_json_objects when ambiguous
missing_schema_version
missing_slides
slides_not_array
```

### Codex prompt

```text
Implement a robust JSON extraction and parsing result for GigaChat slide planning. Return a typed result with success payload or structured sanitized parse error. Do not return only None. Add tests for plain JSON, fenced JSON, explanatory text around JSON, malformed JSON, missing object and ambiguous multiple objects. Do not log raw responses.
```

### Negative prompt

```text
Do not use unsafe eval. Do not parse by fragile regex only. Do not store or log full raw model response. Do not collapse all parser failures into llm_plan_invalid.
```

## D. Retry and repair behavior

### Goal

Add one repair attempt for invalid LLM plans.

### Acceptance criteria

```text
Attempt 1 uses strict generation prompt.
If invalid, exactly one repair attempt is made.
Repair prompt includes schema, requested slide count and sanitized validation errors.
If repair succeeds, metadata shows llm_planning_used=true and llm_attempt_count=2.
If repair fails, fallback may run but metadata shows degraded=true and final error code.
No infinite retry.
```

### Codex prompt

```text
Add one bounded repair attempt to KR-6D LLM slide planning. Use sanitized validation errors, schema contract and requested slide count. Keep prompt/user data handling safe. Preserve deterministic fallback as a degraded fallback only after attempts are exhausted. Add tests with a fake LLM returning invalid first response and valid repair response.
```

### Negative prompt

```text
Do not loop indefinitely. Do not hide repair failure. Do not claim LLM success when fallback is used. Do not log raw prompts or secrets.
```

## E. Sanitized diagnostics and planning metadata

### Goal

Make failures actionable without leaking secrets or private content.

### Acceptance criteria

Planning metadata includes:

```text
planning_mode
llm_planning_used
llm_attempt_count
llm_final_error_code
llm_validation_errors
requested_slide_count
actual_slide_count
schema_version
prompt_echo_blocked
placeholder_leakage_blocked
template_label_leakage_blocked
raw_llm_response_logged=false
```

Validation errors include only safe fields:

```text
code
path
expected
observed_type
observed_count
```

### Codex prompt

```text
Extend KR-6D planning metadata with sanitized diagnostics. Do not include Authorization Key, tokens, client secret, full prompt or raw LLM response. Use safe codes/counts/types and optional hashes/lengths. Ensure fallback metadata is honest and degraded. Add tests that inspect metadata for invalid, repaired and fallback cases.
```

### Negative prompt

```text
Do not put raw response text into planning_metadata. Do not include full user prompt. Do not include secrets. Do not replace actionable codes with a single llm_plan_invalid.
```

## F. User-visible PPTX quality gate

### Goal

Verify the real PPTX text, not only internal outline JSON.

### Acceptance criteria

For the standard user request about implementing KW Studio in a company:

```text
PPTX has exactly 6 slides.
No Additional insight.
No Local deterministic slide image generation.
No Key points.
No Option A / Current path.
No Step 1 as public template label.
No full prompt echo.
No title truncated at comma, preposition or conjunction.
Each slide has a unique business-readable title.
Each slide has 2..5 meaningful bullets.
Text is relevant to KW Studio implementation.
PPTX opens through python-pptx.
PPTX renders through LibreOffice -> PDF -> PNG when render QA is part of the check.
```

### Codex prompt

```text
Add a PPTX public-text quality gate for KR-6D. Extract text from the generated PPTX using python-pptx in tests. Assert absence of known template/internal labels and prompt echo. Assert exact slide count and meaningful public text. Do not rely only on API JSON. Preserve render/visual QA bundle contracts.
```

### Negative prompt

```text
Do not only test planning_metadata. Do not whitelist known bad labels. Do not skip PPTX extraction because the internal outline looks correct.
```

## G. Honest fallback quality

### Goal

Keep deterministic fallback reliable but transparent.

### Acceptance criteria

```text
Fallback runs only after LLM attempts are exhausted or LLM is unavailable.
Fallback exact slide count.
Fallback public text contains no template labels or prompt echo.
Metadata shows degraded=true.
Output text does not imply full LLM success.
Quality report or planning_metadata explains fallback reason safely.
```

### Codex prompt

```text
Harden deterministic fallback so it remains usable but honest. Remove any public template labels from fallback output. Ensure degraded metadata is explicit. Update tests to prove fallback does not masquerade as LLM success. Preserve source-mode routing.
```

### Negative prompt

```text
Do not remove fallback entirely. Do not make fallback look like LLM success. Do not let fallback hide validation errors.
```

## H. Source-mode compatibility

### Goal

Preserve KR-6C routing and legacy/source-aware contracts.

### Acceptance criteria

```text
Real user prompt generation uses KR-6D planner.
Short prompt-only legacy/source-like input uses legacy outline-first planner.
Uploaded/stored/document/presentation source flows preserve source fragments.
Direct internal calls with source_refs or non-default template preserve legacy baseline behavior.
K2 source-aware tests continue to pass.
RF2/RF2.1 media baseline continues to pass.
```

### Codex prompt

```text
Integrate KR-6D planner without globally replacing legacy/source-aware planning. Preserve source-mode routing. Run existing source-mode, K2, RF2 and RF2.1 tests. Add a regression test proving KR-6D planner is selected only for explicit real-user presentation generation intent.
```

### Negative prompt

```text
Do not route all SlidesService.generate_deck calls through the new LLM planner. Do not break uploaded/stored source evidence. Do not remove media assets required by RF2.1.
```

## I. Secret safety

### Goal

Prove KR-6D does not leak secrets or raw private content.

### Acceptance criteria

```text
No Authorization Key in logs.
No access token in logs.
No GIGACHAT_CLIENT_SECRET in logs.
No POSTGRES_PASSWORD in logs.
No full raw LLM response in logs.
No full raw prompt in logs.
Diagnostics use codes/counts/types/hash/length only.
Tests include representative secret-like strings and assert they are not emitted.
```

### Codex prompt

```text
Add or update tests that prove KR-6D diagnostics and metadata do not leak secrets or raw LLM responses. Keep diagnostics actionable through structured codes. Ensure logs and artifacts remain redacted. Do not add secret values to fixtures except safe fake strings used for negative assertions.
```

### Negative prompt

```text
Do not print raw env. Do not dump model response to logs. Do not attach full prompt to quality reports.
```

## J. Acceptance closure

### Targeted checks before runner is handed to the operator

```bash
python -m py_compile <changed Python files>
pytest -q backend/tests/workflows/test_slides_real_user_prompt_quality.py
pytest -q backend/tests/workflows/test_slides_user_prompt_media_baseline.py
pytest -q backend/tests/workflows/test_slides_source_mode_routing.py
pytest -q backend/tests/workflows/test_slides_llm_plan_validation.py
pytest -q backend/tests/workflows/test_slides_llm_plan_repair.py
pytest -q backend/tests/workflows/test_slides_pptx_public_text_quality.py
pytest -q backend/tests/api/test_k1_valid_pptx_generator.py
pytest -q backend/tests/api/test_k2_source_aware_presentation_generation.py
pytest -q backend/tests/api/test_n6_slides_api_schema_stabilization.py
pytest -q backend/tests/api/test_n7_slides_product_regression.py
pytest -q backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py
pytest -q backend/tests/smoke/test_rf2_closure_slides_runtime.py
pytest -q backend/tests/smoke/test_public_gigachat_test_mode.py
python scripts/kw_slides_runtime_inventory_check.py --require-ready --json
python scripts/kw_slides_rf2_closure_check.py --require-ready --json
python scripts/kw_slides_render_visual_qa_bundle_check.py --require-ready
python scripts/kw_project_migration_handoff_check.py --require-ready
git diff --check
```

### Final closure

```text
TARGETED PASS
commit
full runner PASS
Docker smoke PASS
real public_internet_test operator run
PPTX evidence review
push
remote verification
REMOTE ACCEPT / CLOSED
```

### Codex prompt

```text
Create a KR-6D patch only after all relevant targeted tests pass. Do not claim completion until project full runner and Docker smoke have passed on committed HEAD and remote verification is complete. Include logs and evidence paths. Update PROJECT_MIGRATION_HANDOFF.md with the final KR-6D contract and any new runner behavior.
```

### Negative prompt

```text
Do not stop at targeted tests. Do not skip Docker smoke. Do not skip real public_internet_test evidence. Do not claim REMOTE ACCEPT without push and remote verification.
```
