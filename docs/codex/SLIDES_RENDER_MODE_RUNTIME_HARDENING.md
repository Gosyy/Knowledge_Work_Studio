# RF2.5 Slides Adaptive/Template Render Mode Runtime Hardening

## Status

RF2.5 hardens the existing approved-plan and saved-plan retry runtime paths so render-mode handling is explicit, local-only, and safe.

RF2.5 is still Runtime Foundation work. It does not claim Kimi-level slide quality and does not start K-phase.

## Runtime path hardened

RF2.5 adds a shared render-mode runtime policy layer:

```text
approved/saved PresentationPlan
→ explicit render_mode
→ local template policy validation
→ deterministic PPTX render
→ artifact/snapshot/retry lifecycle metadata
```

The hardened policy supports:

- `adaptive` render mode;
- `template` render mode;
- local bundled template registry enforcement;
- default local template resolution for adaptive mode;
- explicit local `template_id` requirement for template mode;
- safe metadata that records layout policy and template source;
- rejection of URL/path/external template references.

## Safety guarantees

RF2.5 guarantees:

- no external template download;
- no browser runtime;
- no public API endpoint;
- no DB schema migration;
- no queue/event-store migration;
- no dependency version change;
- no Dockerfile change;
- no LLM topology change;
- no visual QA runtime;
- no provenance manifest emission yet.

## Runtime metadata

Generated approved-plan and retry results include safe render-mode metadata:

- `render_mode_runtime_hardened`;
- `render_mode`;
- `template_id`;
- `template_source`;
- `layout_policy`;
- `template_id_required`;
- `template_locked`;
- `adaptive_layout_selection_enabled`;
- `external_template_download_allowed`;
- `local_template_registry_enforced`.

## Non-goals

RF2.5 does not:

- improve visual layout quality to Kimi-level;
- add a full deck editor;
- add remote template catalogs;
- fetch templates from the internet;
- add local GigaChat planning;
- emit downloadable provenance manifests;
- implement visual QA runtime;
- change frontend runtime;
- change dependencies;
- run `npm audit fix` or `npm audit fix --force`.

RF2.5 is required infrastructure for Kimi-level adaptive/template UX, but it does not reach Kimi-level.

## Acceptance

RF2.5 is accepted when:

- `python3 scripts/kw_slides_render_mode_runtime_check.py --repo-root . --require-ready --json` passes;
- RF2.5 smoke tests prove adaptive and template runtime behavior;
- approved-plan and saved-plan retry paths both carry render-mode policy metadata;
- external/path/unknown template references are rejected;
- production readiness includes RF2.5;
- full post-RF2.5 runner and Docker runtime smoke pass before final acceptance.
