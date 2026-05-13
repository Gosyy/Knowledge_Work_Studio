# RC5 Final Release Readiness Dossier

RC5 is the final release-readiness dossier checkpoint for the accepted K/RC/RCH baseline on branch `8_K_Phase`.

It is intentionally documentation/checker/test/gate scope only. It does not add product runtime behavior, API endpoints, database migrations, frontend runtime changes, dependency changes, Docker changes, cloud LLM, cloud vision, or Kimi-level claims.

## Purpose

RC5 turns the already accepted K0-K6, K-phase closure, RC1-RC4, and RCH1-RCH3 evidence into one operator-readable and machine-readable release dossier.

The dossier records:

- accepted checkpoint inventory;
- required docs, checkers, and tests;
- production readiness gate inclusion;
- known limitations;
- no-scope guarantees;
- remaining human review and production topology verification requirements.

## Known limitations intentionally kept open

- Human benchmark review is still required before stronger product-quality claims.
- RC3 public GigaChat development route is not production Server 3 offline topology evidence.
- Whole-project Kimi-level parity is not claimed.
- Dependency/security remediation remains a separate controlled patch.

## Acceptance

RC5 is accepted only when:

- `scripts/kw_rc5_final_release_readiness_dossier.py --require-ready --json` reports `ready`;
- RC5 smoke test passes;
- production readiness gate includes RC5;
- full runner passes;
- Docker smoke passes.
