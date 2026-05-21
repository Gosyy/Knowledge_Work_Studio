# RC4 — Release candidate artifact pack

## Status

RC4 is a release-candidate checkpoint after RCH1, RCH2, and RCH3. It packages the accepted K-phase, RC, and RCH evidence into a machine-readable artifact inventory and an operator-facing report.

RC4 is not a product feature patch. It does not add runtime behavior, public API endpoints, DB schema migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or Kimi-level claims.

## Purpose

RC4 answers one release-readiness question:

```text
Do we have a complete, machine-readable evidence pack for K0-K6, K-phase closure, RC1-RC3, and RCH1-RCH3?
```

The checkpoint verifies that every accepted stage has:

- a codex document;
- an executable checker;
- a smoke/regression test;
- a release-candidate artifact role;
- safe no-scope metadata.

## Outputs

When invoked with `--artifacts-dir`, RC4 writes:

- `rc4-release-candidate-artifact-pack.json`;
- `rc4-release-candidate-artifact-pack.md`.

The JSON pack includes:

- branch and commit;
- pack inventory;
- file digests;
- known limitations;
- no-scope flags;
- next recommended step.

## Known limitations tracked by RC4

RC4 intentionally keeps these limitations visible:

- human benchmark review remains required;
- public GigaChat development route is not the production Server 3 offline route;
- whole-product Kimi-level is not claimed;
- dependency/security remediation remains a separate controlled patch.

## Acceptance

RC4 is accepted only when:

- `scripts/kw_rc4_release_candidate_artifact_pack.py --require-ready --json` returns `status=ready`;
- RC4 smoke test passes;
- production readiness gate includes RC4;
- full runner passes;
- Docker smoke passes.
