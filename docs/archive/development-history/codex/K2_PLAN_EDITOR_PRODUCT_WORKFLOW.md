# K2 — Plan Editor as Product Workflow

## Status

K2 starts after accepted K1 on branch `8_K_Phase`.

K2 turns the generated `PresentationPlan` into an operator-editable planning workflow. It does not claim Kimi-level output and does not improve renderer quality by itself.

## Runtime contract

K2 input:

- K1 `PresentationPlan`;
- optional source/evidence links by slide;
- operator edit requests;
- render mode controls;
- approval intent.

K2 output:

- editable plan editor session;
- append-only safe task event stream;
- versioned slide edits;
- approval gate before conversion back to `PresentationPlan`;
- safe metadata for production readiness and later K3/K5 integrations.

## Product workflow covered by K2

K2 supports:

- editable outline;
- slide intent editing;
- evidence/source link editing;
- visual intent editing;
- render mode controls;
- template mode requiring explicit local `template_id`;
- diff/retry workflow metadata;
- task event visibility;
- clear failure states;
- approval gate before generation.

## Non-goals

K2 does not:

- add a public API endpoint;
- add a DB schema migration;
- change frontend runtime;
- change dependency versions;
- change Dockerfiles;
- add visual QA runtime;
- improve renderer quality;
- add cloud LLM fallback;
- claim Kimi-level support.

## Safety

K2 stores safe metadata only:

- digests and ids;
- event types and sequence numbers;
- counts and render-mode controls;
- no raw prompt;
- no raw source text;
- no secret-like values.

## Acceptance

K2 is accepted when:

- checker reports `status: ready`;
- unapproved sessions cannot be converted into `PresentationPlan`;
- slide title/bullets/intent/evidence/visual intent edits are applied;
- template mode rejects missing local `template_id`;
- event order is append-only and safe;
- production readiness includes K2;
- full runner and Docker smoke pass.
