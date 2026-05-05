# P9 Product Release Hardening Plan

P9 starts from the accepted K/RC/RCH baseline on branch `8_K_Phase` at `a2f1aa90fbc56531de85a953447f61a52a63efb7`.

P9 is not a new product-runtime phase by default. It is a release-hardening track for evidence, human review, production topology verification, and focused quality fixes derived from accepted benchmark findings.

## Accepted source baseline

- K0-K6 closed.
- K-phase closure closed.
- RC1-RC5 accepted.
- RCH1-RCH4 accepted.
- KRC final branch closure accepted.

## P9-1 — Golden benchmark human review results

P9-1 captures completed human review results for the five golden benchmark artifacts generated from the closed K/RC/RCH baseline.

The review results are intentionally conservative: all five generated decks are marked `request_rework`. This does not mean the runtime failed. It means the decks are not yet strong enough for product-quality claims because they still show generic fallback labels, weak decision-table treatment, incomplete semantic coverage in some cases, and evidence/provenance usability gaps.

## Scope guard

P9-1 does not add product runtime logic, API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or Kimi-level claims.

## Next hardening direction

The first follow-up patch should be selected from tracked human-review findings, preferably renderer/planning hardening for generic fallback labels, comparison-table decision matrix handling, and filler-slide prevention.
