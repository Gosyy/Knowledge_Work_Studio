# RF2.6 Slides Provenance Manifest Runtime

## Status

RF2.6 emits a real downloadable provenance manifest artifact for the approved-plan generation path and the saved-plan retry path.

This is still Runtime Foundation work. RF2.6 does not claim Kimi-level slide quality and does not start K-phase.

## Runtime paths added

RF2.6 adds additive service methods over the existing RF2.3/RF2.4 runtime paths:

```text
approved PresentationPlan
→ RF2.3 lifecycle render
→ PPTX artifact registration
→ plan snapshot persistence
→ append-only safe event refs
→ downloadable provenance JSON artifact
```

```text
saved PresentationPlanSnapshot
→ RF2.4 retry lifecycle render
→ retry PPTX artifact registration
→ new plan snapshot persistence
→ retry parent links
→ append-only safe event refs
→ downloadable provenance JSON artifact
```

## What the manifest links

Each RF2.6 manifest links:

- session id;
- task id;
- presentation id;
- plan snapshot id;
- render mode and local template policy metadata;
- generated PPTX artifact id, filename, content type, storage backend, and size;
- append-only task event refs;
- artifact checksum;
- manifest digest;
- safe redaction policy.

Retry manifests also link:

- parent task id;
- parent saved plan snapshot id;
- parent presentation version id when present;
- retry instruction digest only;
- new plan snapshot id;
- new artifact id.

Raw operator instruction text is not stored in the manifest.

## Non-goals

RF2.6 does not add:

- a public API endpoint;
- DB schema migration;
- queue/event-store migration;
- visual QA runtime;
- browser runtime;
- LLM topology changes;
- dependency version changes;
- Dockerfile changes;
- Kimi-level claims.

RF2.6 is required infrastructure for Kimi-level provenance UX, but it does not reach Kimi-level.

## Acceptance

RF2.6 is accepted when:

- `python3 scripts/kw_slides_provenance_manifest_runtime_check.py --repo-root . --require-ready --json` passes;
- RF2.6 smoke tests prove generation and retry manifest artifact emission;
- prior RF2.2-RF2.5 checks still pass;
- production readiness includes RF2.6;
- full post-RF2.6 runner and Docker runtime smoke pass before the verdict commit is considered fully accepted.
