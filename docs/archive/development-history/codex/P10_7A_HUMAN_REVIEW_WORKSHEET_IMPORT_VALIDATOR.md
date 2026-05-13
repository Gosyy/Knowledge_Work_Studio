# P10-7a — Human review worksheet import validator

- status: `controlled_review_results_import_validator`
- branch: `9_Product_Release_Hardening`
- baseline before P10-7a: `8c5b08bb11ac847fd5a165782f68081029ef43c5`
- Kimi-level claimed: `False`

## Purpose

P10-7a adds a conservative validator for completed post-P9 human re-review worksheets. It is a tooling and schema checkpoint, not the P10-7 ingest step.

The validator exists because P10-5 and P10-6 correctly keep the release decision deferred while the five P10-4 worksheets remain pending. P10-7a makes the future ingest safer by checking a reviewer-supplied JSON file, directory, or P10-6 ZIP packet before any approval-state change is considered.

## Validation contract

A completed review import must contain exactly the five golden benchmark case IDs. Every worksheet must provide:

- `reviewer_id` as a non-empty string;
- `reviewed_at` as an ISO-8601 timestamp;
- `decision` as one of `approve`, `request_rework`, or `reject`;
- `scores` for every P9/P10 review dimension;
- `slide_level_findings` as a list;
- `follow_up_backlog` as a list.

`request_rework` and `reject` decisions must include a non-empty follow-up backlog. `approve` decisions are rejected if any review dimension has a blocking score of 2 or lower.

The validator rejects imported payloads that attempt to set approval, Kimi-level, auto-approval, or Server 3 offline/intranet proof flags. Those decisions remain outside P10-7a.

## Operator usage

Static contract self-check:

```bash
python3 scripts/kw_p10_7a_human_review_worksheet_import_validator.py \
  --repo-root . \
  --require-ready \
  --json
```

Validate a completed reviewer payload:

```bash
python3 scripts/kw_p10_7a_human_review_worksheet_import_validator.py \
  --repo-root . \
  --review-results logs/p10-6-human-review-packet-completed.zip \
  --require-ready \
  --json
```

The validator reads JSON, directories containing JSON files, or ZIP packets containing JSON files. It selects the JSON payload with the most review worksheets and validates it.

## Decision boundary

P10-7a does not ingest completed results into a release dossier. It does not approve or reject the release, does not approve any deck, and does not claim Kimi-level parity.

The supported release decision remains `defer_pending_human_re_review` until a later P10-7 ingest patch runs against real completed, validator-passing human review results.

P10-5a public API GigaChat evidence remains real provider evidence for `public_api_dev`, but it is not production Server 3 offline/intranet proof.

## Non-goals

P10-7a does not add API endpoints, database migrations, frontend runtime changes, dependency or lockfile changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or dependency/security remediation. It does not run `npm audit fix --force`.

## Acceptance

P10-7a is accepted when the validator reports `ready` for its static contract self-check, rejects pending/incomplete worksheets, accepts a complete synthetic reviewer payload in smoke tests, targeted pytest passes, production readiness includes P10-7a, the full runner passes with only known non-blocking warnings, and Docker smoke passes on profile 2.

