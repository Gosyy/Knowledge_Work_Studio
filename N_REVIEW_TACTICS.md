# N_REVIEW_TACTICS.md

## Purpose

This document defines the review tactics for the accepted slides product workflow after M9-M15 and N1-N6.

Accepted baseline:
- M9-M15: accepted slides subsystem foundation.
- N1: presentation retrieval API accepted.
- N2: deck revision API accepted.
- N3: revision persistence integration tests accepted.
- N4: slide revision strategy accepted.
- N5: sample deck export smoke tests accepted.
- N6: slides API schema stabilization accepted.

N7 does not add new product capabilities. It locks regression coverage and future review rules.

---

## Must-preserve workflow paths

Future slides changes must not regress these paths:

1. Prompt-only synchronous slides generation
2. Stored-source/source-grounded slides generation
3. Queued slides generation
4. PPTX artifact download and package validity
5. Structured business blocks in generated PPTX
6. Generated media metadata shape
7. Source grounding metadata shape
8. Presentation retrieval API
9. Deck revision API
10. Revision lineage
11. Revision persistence
12. Stable public slides result schema

---

## Hard rejection conditions

Reject a patch if it:

- breaks `python3 -m pytest -q`
- breaks `python3 -m compileall backend`
- removes M9-N7 regression coverage without stricter replacement
- exposes `storage_key`, `storage_uri`, local filesystem paths, or internal storage implementation details in public slides schemas
- silently falls back from provider-backed logic to fake deterministic success in production paths
- claims visual/OCR/source extraction capability that is not implemented honestly
- adds public internet dependency to offline/intranet deployment
- changes frontend outside explicit scope
- rewrites accepted slides planning/layout/media/revision architecture without issue approval
- stores binary files primarily in metadata repositories
- makes SQLite a production truth layer
- creates route-local service wiring that bypasses the composition root
- adds fake success paths for missing plans, missing sources, missing storage, or failed providers

---

## Required review checklist for future slides patches

### Scope

- Does the patch implement only the named issue?
- Are adjacent issues explicitly untouched?
- Are production-code changes necessary, or would test/doc changes be enough?

### Architecture

- Does wiring go through the accepted composition root?
- Are repository/storage/provider abstractions preserved?
- Are service-level boundaries still clear?

### API safety

- Are public schemas explicit?
- Are unsafe storage internals hidden?
- Is backward compatibility preserved for existing `result_data` fields?

### Source grounding

- Are source refs honest?
- Are citations tied to available extracted text or accepted derived content?
- Is unsupported visual/OCR grounding rejected rather than faked?

### Revision flow

- Does revision create a new `StoredFile` and `PresentationVersion`?
- Is `Presentation.current_file_id` advanced intentionally?
- Is lineage ordered and inspectable?
- Does provider-backed revision fail honestly?

### PPTX output

- Is the generated artifact a valid PPTX zip package?
- Are slide XML, relationships, media, and structured blocks preserved?
- Are sample decks deterministic where expected?

### Tests

At minimum, future slides product changes must consider:

```bash
python3 -m pytest backend/tests/api/test_n7_slides_product_regression.py -q
python3 -m pytest backend/tests/smoke/test_n5_sample_deck_export.py -q
python3 -m pytest backend/tests/api/test_n6_slides_api_schema_stabilization.py -q
python3 -m pytest backend/tests/api/test_n2_deck_revision_api.py -q
python3 -m pytest backend/tests/integrations/test_n3_revision_persistence.py -q
python3 -m pytest -q
python3 -m compileall backend
```

---

## N7 regression coverage map

| Path | Covered by |
|---|---|
| prompt-only sync deck | `test_n7_sync_prompt_only_slides_generation_regression` |
| queued deck | `test_n7_queued_slides_generation_regression` |
| source-grounded deck | `test_n7_source_grounded_slides_generation_regression` |
| structured blocks | `test_n7_structured_blocks_are_present_in_downloaded_pptx` |
| presentation retrieval | `test_n7_presentation_retrieval_and_revision_api_regression` |
| revision API | `test_n7_presentation_retrieval_and_revision_api_regression` |
| revision lineage | `test_n7_presentation_retrieval_and_revision_api_regression` |
| public schema | `SlidesTaskResultDataSchema` assertions |
| unsafe storage leakage | N6 schema tests |
| optional visual smoke | N5 smoke tests |
