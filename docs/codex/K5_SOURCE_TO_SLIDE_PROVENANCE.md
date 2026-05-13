# K5 — Source-to-slide provenance runtime

## Status

K5 adds a controlled local runtime layer for source-to-slide provenance on branch `8_K_Phase` after accepted K4.

K5 does not claim KW Studio is Kimi-level. Kimi-level remains gated by K6 end-to-end workflow and the K0 benchmark gates.

## Goal

Make every generated slide traceable to bounded, deterministic source evidence without adding cloud dependencies, public endpoints, database migrations, frontend runtime changes, dependency changes, or Dockerfile changes.

K5 works with the existing RF2.6 downloadable provenance manifest runtime and the existing source-grounding/citation footer renderer. It adds a K-phase layer that produces:

- normalized source descriptors;
- bounded source fragments;
- fragment digests;
- slide-level evidence links;
- enriched `PresentationPlan` slide citations;
- source citation footer render support through existing PPTX renderer behavior;
- a source-to-slide manifest section;
- coverage metadata for operator review;
- safe metadata that stores digests and identifiers, not raw source text.

## Runtime scope

Implemented runtime module:

- `backend/app/services/k_phase/source_to_slide_provenance.py`

Validation:

- `scripts/kw_k5_source_to_slide_provenance_check.py`
- `backend/tests/smoke/test_k5_source_to_slide_provenance.py`

Production readiness integration:

- `scripts/kw_production_readiness_gate.py`

## Runtime contract

The main K5 runtime accepts:

- an approved or render-ready `PresentationPlan`;
- source text already available inside the local workflow;
- optional source references such as file/document/presentation IDs, locators, roles, and checksum digests.

It returns:

- a `PresentationPlan` enriched with `SlideCitation` entries;
- deterministic source fragments with bounded excerpt previews and `sha256:` digests;
- one slide evidence link per slide;
- a complete coverage report;
- a K5 manifest section that can be attached to the existing RF2.6 manifest copy;
- safe runtime metadata.

## Redaction policy

K5 safe metadata follows `bounded_excerpt_preview_and_digest_only`:

- raw source text is not stored in safe metadata;
- raw prompts are not stored;
- sensitive-looking values are redacted from safe source descriptors;
- manifest evidence uses bounded excerpt previews and digests;
- full source text remains outside K5 safe metadata and outside the K5 checker report.

## Relationship to RF2.6

RF2.6 already emits downloadable provenance manifest artifacts linking plan snapshots, render attempts, event refs, and PPTX artifacts.

K5 does not replace RF2.6. It adds the missing slide-level source evidence section:

- `source_to_slide_provenance.sources`
- `source_to_slide_provenance.source_fragments`
- `source_to_slide_provenance.slide_evidence_links`
- `source_to_slide_provenance.coverage`
- `source_to_slide_provenance.integrity.section_digest`

The helper `attach_k5_provenance_to_manifest()` returns a manifest copy with this section and a K5 section digest. It does not pretend to re-sign the already emitted RF2.6 artifact manifest in this patch.

## Relationship to K3 and K4

K5 is intended to run after K3 renderer-quality bounding and before or alongside K4 visual QA of the rendered PPTX.

K5 verifies that provenance citations survive rendering by relying on existing PPTX citation footer generation. K5 does not add visual QA; K4 remains the visual QA runtime.

## Non-goals

K5 intentionally does not add:

- public API endpoint;
- database schema migration;
- frontend runtime change;
- dependency version change;
- Dockerfile or base image change;
- cloud LLM;
- cloud vision;
- K6 end-to-end workflow;
- Kimi-level claim.

## Acceptance signal

K5 is accepted when:

- K5 targeted runner passes;
- K0-K5 checkers pass;
- targeted smoke tests pass;
- production readiness targeted gate passes;
- functional K5 commit is made;
- empty `K5 verdict: ACCEPT` commit is made;
- branch `8_K_Phase` is pushed;
- full runner passes after push;
- Docker compose smoke passes after push.
