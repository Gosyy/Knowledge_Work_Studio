# K-phase release readiness checkpoint

Status: implemented as a non-feature closure checkpoint after K6.

This checkpoint verifies that the controlled K-phase route is closed and ready for a release-candidate style validation pass. It does not add user-facing runtime capability, API surface, database schema, frontend runtime, dependency versions, Dockerfiles, cloud LLM, or cloud vision.

## Scope

The checkpoint covers the accepted K-phase route:

- K0 — Kimi-level rubric and golden benchmark;
- K1 — local GigaChat planning engine;
- K2 — plan editor product workflow;
- K3 — renderer quality runtime;
- K4 — visual QA runtime;
- K5 — source-to-slide provenance runtime;
- K6 — end-to-end Kimi-like workflow.

## Release-readiness checks

`scripts/kw_k_phase_release_readiness_check.py` verifies:

- all required K0-K6 docs, services, checker scripts, and smoke tests are present;
- each K0-K6 checker reports `status: ready`;
- K6 verdict commit is an ancestor of the checked tree when git metadata is available;
- branch and K6 ancestry guards are valid when `--require-ready` is used;
- the route is ready for release-candidate validation;
- closure does not claim unqualified whole-product Kimi-level;
- closure does not add feature scope.

## Non-scope guarantees

K-phase closure intentionally does not add:

- public API endpoint;
- DB schema migration;
- frontend runtime change;
- dependency version change;
- Dockerfile or base image change;
- cloud LLM or cloud vision;
- new feature runtime beyond the already accepted K0-K6 checkpoints.

## Product claim boundary

K6 closes the end-to-end Kimi-like workflow checkpoint, but the release-readiness checkpoint keeps `whole_project_kimi_level_supported: false` and `kimi_level_claimed_by_k_phase_closure: false`.

This means KW Studio now has an accepted offline/intranet K-phase route from source to plan, approval, rendering, visual QA, provenance, and operator delivery, but it must not be described as unqualified full Kimi-level.

## Operator flow

After this checkpoint passes targeted validation, the operator should:

1. commit `K-phase closure: release readiness checkpoint`;
2. add an empty verdict commit `K-phase closure verdict: ACCEPT`;
3. push `8_K_Phase`;
4. run the full profile runner;
5. run Docker Compose smoke;
6. only then treat the K-phase route as release-readiness closed.
