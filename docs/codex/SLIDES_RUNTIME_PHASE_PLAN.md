# KW Studio RF2 Slides Runtime Phase Plan

## Status

RF2.0 checkpoint: slides runtime phase kickoff and scope guard.

This checkpoint starts RF2 after RF1 offline/intranet foundation closure. RF2 is the product-value stream focused on turning the accepted S-phase slides contracts into a working offline slides runtime. RF2.0 itself is a planning and policy checkpoint only: it does not change renderer behavior, task execution behavior, persistence semantics, dependency versions, Dockerfiles, LLM configuration, browser runtime, or document/PDF runtime.

## Why RF2 now

RF1 closed the operator foundation: dependency inventory, offline bootstrap bundle strategy, manifest validation, template tooling, artifact presence checks, checksum integrity, inventory summaries, readiness report, command groups, and RF1 closure policy.

The next highest product-value stream is slides because the S-phase already established:

- plan-first UX contract;
- task event stream and saved-plan retry contract;
- frontend slides plan editor;
- adaptive/template render mode contract;
- source-to-artifact provenance manifest contract;
- browser evidence and visual QA planning links that can later support richer artifact verification.

RF2 turns these contracts into runtime behavior incrementally, without breaking offline/intranet constraints.

## RF2 goals

RF2 should produce a real offline slides workflow that can:

1. accept an operator-approved slides plan;
2. generate a downloadable PPTX artifact deterministically enough for smoke tests;
3. register artifact history and plan snapshots;
4. emit safe task events;
5. support regenerate-from-saved-plan behavior;
6. preserve adaptive/template mode metadata;
7. produce source-to-artifact provenance for generated decks;
8. stay offline/intranet-first with local GigaChat as the default LLM path.

## RF2 non-goals

RF2 must not:

- replace local GigaChat with LiteLLM;
- silently switch to cloud/external LLMs;
- introduce internet-dependent default runtime;
- become a general autonomous browser agent;
- become a broad file-format zoo;
- rewrite the app as microservices;
- change Docker/offline dependency policy created in RF1;
- run `npm audit fix --force` as part of slides runtime;
- introduce large renderer rewrites without a narrow acceptance gate.

## Runtime scope guard

RF2 should prefer narrow runtime increments:

- inspect current slides service and API behavior before changing it;
- add deterministic smokeable behavior before LLM-dependent behavior;
- keep generated artifacts downloadable and registered;
- preserve plan-first gates;
- keep safe payload redaction in task events;
- keep provenance as a first-class artifact;
- keep frontend UX changes small and testable.

## Proposed RF2 steps

### RF2.1 — Slides runtime capability inventory and baseline smoke

Inventory the current runtime implementation and tests for:

- presentations API;
- slides service;
- plan inspect/revision behavior;
- artifact registration;
- frontend e2e coverage;
- deterministic fixture generation possibilities.

Acceptance should produce a report/checker that clearly states what already works and what still needs runtime implementation.


### RF2.1 — Slides runtime capability inventory and baseline smoke

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.1 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.1 verdict: ACCEPT` commit.

Scope:
- inventory current slides service/API/frontend/test runtime surfaces;
- run a no-network baseline PPTX smoke through existing `SlidesService.generate_deck`;
- classify capabilities as baseline-runtime-ready, partial runtime, product gap, or contract-only;
- explicitly record that the current deterministic generator is not proven Kimi-grade;
- explicitly record that the whole slides product loop is not proven Kimi-level;
- prepare the RF2.2 handoff for deterministic PPTX generation from an approved plan.

Non-goals:
- do not claim Kimi-level slides quality from generator existence alone;
- do not treat generator maturity as whole-project maturity;
- do not change renderer behavior;
- do not change service/API behavior;
- do not change persistence behavior;
- do not change frontend behavior;
- do not change dependency versions;
- do not change Dockerfiles;
- do not change LLM topology;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_runtime_inventory_check.py --repo-root . --require-ready --json` passes;
- checker reports `kimi_grade_supported: false`;
- checker reports `current_generator_grade: baseline_deterministic_not_kimi_grade`;
- checker reports `whole_project_kimi_level_supported: false`;
- checker reports `product_loop_grade: baseline_inventory_not_kimi_level_project`;
- `python3 -m pytest backend/tests/smoke/test_rf2_1_slides_runtime_inventory.py -q` passes;
- selected existing slides service PPTX smoke passes;
- S3-S7 slides contract checks pass;
- RF2.0 checkpoint check passes;
- production readiness includes the RF2.1 inventory checkpoint;
- full post-RF2.1 runner and Docker runtime smoke pass before final acceptance.

### RF2.2 — Minimal deterministic PPTX generation from approved plan

Add or harden a minimal offline PPTX generation path from an approved plan.

Non-goal: no new AI dependency and no renderer rewrite.


### RF2.2 — Minimal deterministic PPTX generation from approved plan

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.2 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.2 verdict: ACCEPT` commit.

Scope:
- add an additive backend runtime path for approved `PresentationPlan` rendering;
- introduce `ApprovedPlanRenderRequest` and `ApprovedPlanRenderResult`;
- add `render_approved_plan_to_pptx`;
- add `SlidesService.generate_deck_from_approved_plan`;
- return deterministic PPTX bytes, sha256, size, slide count, render mode, template id, safe metadata, and safe event hints.

Non-goals:
- do not add a public API endpoint yet;
- do not persist generated artifacts yet;
- do not emit downloadable provenance manifest yet;
- do not implement saved-plan retry yet;
- do not implement visual QA runtime;
- do not claim Kimi-level slides quality;
- do not change dependency versions;
- do not change Dockerfiles;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_approved_plan_runtime_check.py --repo-root . --require-ready --json` passes;
- smoke tests prove deterministic approved-plan PPTX rendering;
- unapproved plans are rejected;
- template mode requires explicit local template id;
- production readiness includes RF2.2;
- full post-RF2.2 runner and Docker runtime smoke pass before final acceptance.


### RF2.2a — RF-to-K transition guard and Kimi-level Product Power roadmap

RF2.2a establishes the transition guard between RF and the later K-phase.

RF2.2a confirms:
- Kimi-level is deferred to K-phase;
- K-phase is for Product Power work, not RF foundation work;
- RF2 must not absorb open-ended K-phase product-power work;
- RF2.3 remains the next runtime implementation step after RF2.2a;
- future new-chat migration prompts must include the RF-to-K route.

RF2.2a does not change slides runtime behavior, dependencies, Dockerfiles, LLM topology, or frontend runtime.

### RF2.3 — Plan snapshot persistence and task event stream runtime wiring

Make runtime registration of plan snapshots and safe task events concrete where it is currently contract-only.


### RF2.3 — Plan snapshot persistence and task event stream runtime wiring

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.3 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.3 verdict: ACCEPT` commit.

Scope:
- wire RF2.2 approved-plan render output into an additive lifecycle runtime;
- introduce `render_approved_plan_with_lifecycle`;
- persist approved `PresentationPlan` through `PresentationPlanSnapshotService`;
- register the generated PPTX through the existing artifact service path;
- emit an append-only safe task event tuple following the S4 slides event contract;
- wire official composition so `SlidesService` receives plan snapshot and artifact services.

Non-goals:
- do not add a public API endpoint yet;
- do not add a DB schema migration;
- do not implement saved-plan retry yet;
- do not emit the downloadable provenance manifest yet;
- do not implement visual QA runtime;
- do not improve renderer quality to Kimi-level;
- do not change dependencies;
- do not change Dockerfiles;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_approved_plan_lifecycle_check.py --repo-root . --require-ready --json` passes;
- RF2.3 smoke tests prove snapshot persistence, artifact registration, event order, and safe payload;
- production readiness includes RF2.3;
- full post-RF2.3 runner and Docker runtime smoke pass before final acceptance.

Default next step after RF2.3:
- RF2.4 — Saved-plan retry runtime path.

### RF2.4 — Saved-plan retry runtime path

Implement retry-from-saved-plan behavior using existing plan snapshots and explicit operator instruction.


### RF2.4 — Saved-plan retry runtime path

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.4 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.4 verdict: ACCEPT` commit.

Scope:
- load a saved `PresentationPlanSnapshot`;
- deserialize and validate the saved `PresentationPlan`;
- require explicit operator retry instruction;
- require render mode confirmation;
- regenerate deterministic PPTX bytes from the saved plan;
- register a new artifact through the existing artifact service path;
- persist a new plan snapshot;
- emit the S4 retry event sequence with safe payload only;
- record parent links and retry instruction digest without storing raw operator instruction.

Non-goals:
- do not add a public API endpoint yet;
- do not add a DB schema migration;
- do not add a queue/event-store migration;
- do not emit the downloadable provenance manifest yet;
- do not implement visual QA runtime;
- do not improve renderer quality to Kimi-level;
- do not change dependencies;
- do not change Dockerfiles;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_saved_plan_retry_check.py --repo-root . --require-ready --json` passes;
- RF2.4 smoke tests prove saved snapshot loading, explicit operator instruction, new artifact, new snapshot, retry parent links, retry event order, and safe payload;
- production readiness includes RF2.4;
- full post-RF2.4 runner and Docker runtime smoke pass before final acceptance.

Default next step after RF2.4:
- RF2.5 — Adaptive/template local render mode runtime hardening.

### RF2.5 — Adaptive/template local render mode runtime hardening

Wire render mode metadata into generated artifact output while keeping templates local-only.

### RF2.6 — Slides provenance manifest emitted as downloadable artifact

Generate the provenance manifest as an actual registered artifact linked to the generated PPTX and source plan.

### RF2.7 — Slides runtime closure and readiness for RF2 closure

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.7 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.7 verdict: ACCEPT` commit.

Scope:
- consolidate RF2.0-RF2.6 as the slides runtime foundation;
- add a closure/readiness gate for approved-plan generation, saved-plan retry, local render mode hardening, and downloadable provenance manifests;
- prove generation and retry provenance paths through service-level smoke;
- keep K-phase product-power work deferred.

Non-goals:
- no K-phase work;
- no Kimi-level claim;
- no public endpoint;
- no schema migration;
- no queue/event-store migration;
- no dependency or Docker changes;
- no visual QA runtime;
- no `npm audit fix --force`.

Default next route after RF2.7:
- RF2_closure -> RF3 -> RF4 -> RF_closure -> K0.

## Acceptance policy for RF2.0

RF2.0 is accepted when:

- this phase plan exists;
- `scripts/kw_slides_runtime_phase_check.py --require-ready` passes;
- RF2.0 smoke test passes;
- existing S3-S7 slides contract checks still pass;
- production readiness includes the RF2.0 policy check;
- full post-RF2.0 runner passes;
- Docker runtime smoke with `--skip-build` passes;
- remote `7_Runtime_Foundation` matches the local RF2.0 verdict commit;
- working tree is clean after cleanup.

## Handoff after RF2.0

Do not start RF2.1 until RF2.0 is accepted.

After RF2.0 acceptance, recommended next step:

RF2.1 — Slides runtime capability inventory and baseline smoke.

### RF2.5 — Adaptive/template local render mode runtime hardening

Status: in progress in this patch; accepted only after a functional commit, targeted checks, post-RF2.5 full runner, Docker runtime smoke with `--skip-build`, and a separate `RF2.5 verdict: ACCEPT` commit.

Scope:
- add a shared runtime policy resolver for `adaptive` and `template` render modes;
- enforce local bundled template ids for both approved-plan render and saved-plan retry;
- allow adaptive mode to resolve a local default template when no explicit template id is supplied;
- require explicit local template id for template mode;
- reject URL, filesystem path, traversal, and unknown template references;
- add safe render-mode policy metadata to approved-plan lifecycle and retry metadata.

Non-goals:
- do not add a public API endpoint;
- do not add a DB schema migration;
- do not add queue/event-store migration;
- do not emit downloadable provenance manifest yet;
- do not implement visual QA runtime;
- do not improve renderer quality to Kimi-level;
- do not change dependencies;
- do not change Dockerfiles;
- do not run `npm audit fix --force`.

Acceptance:
- `python3 scripts/kw_slides_render_mode_runtime_check.py --repo-root . --require-ready --json` passes;
- smoke tests prove adaptive/template local-only behavior and safe metadata;
- production readiness includes RF2.5;
- full post-RF2.5 runner and Docker runtime smoke pass before final acceptance.

Default next step after RF2.5:
- RF2.6 — Slides provenance manifest emitted as downloadable artifact.
