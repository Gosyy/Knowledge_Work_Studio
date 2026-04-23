# M9_M15_PHASE_ISSUE_PACK.md

## Purpose

This pack defines the post-M8 slides subsystem roadmap.

Current accepted reality before this pack:
- F–M8 phases are accepted.
- Current slides generation is an outline-first, deterministic, text-only PPTX generator.
- Source extraction and derived content reuse exist after M8.
- This pack moves slides from valid-text-deck generation toward a production-capable presentation subsystem.

## Required implementation order

1. M9 — Presentation planning foundation
2. M10 — Layout/template engine
3. M11 — PPTX media embedding foundation
4. M12 — Image pipeline for slides
5. M13 — Tables, charts, and business slide blocks
6. M14 — Source-aware visual grounding
7. M15 — Deck editing and revision flow

Do not reorder these issues unless an explicit later architecture decision says so.

---

## Cross-issue architectural rules

- Do not redesign accepted F–M8 architecture.
- Do not replace the composition root with route-local wiring.
- Do not reintroduce transitional orchestration surfaces.
- Do not make SQLite a production truth layer.
- Do not store binary files primarily in Postgres.
- Do not activate non-GigaChat providers in the approved deployment profile.
- Do not add public-internet deployment assumptions.
- Do not add fake success paths.
- Do not hide missing infrastructure behind local fallback.
- Do not remove tests merely to make the suite pass.
- Do not touch frontend unless the issue explicitly allows it.

---

## Cross-issue review dimensions

Every M9–M15 issue must be reviewed on:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into the offline intranet profile
- pytest or compileall fails

---

# M9 — Presentation planning foundation

## Goal

Replace primitive sentence-split slide outlining with a typed presentation planning foundation.

## Current problem

Current outline generation is too weak:
- no typed slide roles
- no explicit story arc
- no explicit deck goal/audience/tone
- no robust slide-count policy
- no bullet-bound policies
- no separation between planning and rendering

## Scope

Add:
- `PresentationPlan` model
- `PlannedSlide` model
- typed slide kinds
- deck planner service
- story arc policies
- slide-count policies
- bullet-length policies
- compatibility bridge from typed plan to the current renderer input

## Required minimum slide types

- title
- section
- content
- comparison
- timeline
- data
- conclusion
- appendix

## Allowed changes

- slides planning/domain models
- slides planner logic
- outline compatibility layer
- focused tests

## Likely files

- `backend/app/services/slides_service/outline.py`
- `backend/app/services/slides_service/service.py`
- `backend/app/services/slides_service/entrypoint.py`
- new slides planning modules under `backend/app/services/slides_service/`
- `backend/tests/services/test_slides_service.py`
- new planner-specific tests

## Adjacent issue firewall

- M9 may introduce typed planning models and planner logic.
- M9 must NOT introduce the full layout/template engine. That belongs to M10.
- M9 must NOT add media/image embedding. That belongs to M11.
- M9 must NOT add image generation or retrieval. That belongs to M12.
- M9 must NOT add tables/charts rendering. That belongs to M13.
- M9 must NOT add source-aware visual grounding. That belongs to M14.
- M9 must NOT add revision/update flow. That belongs to M15.

## Hard anti-scope

- Do NOT leave planning as sentence splitting with renamed functions.
- Do NOT hide primitive outline behavior behind a new model name only.
- Do NOT remove deterministic behavior unless replaced with bounded deterministic planning.
- Do NOT change current slides generation behavior except through a compatibility bridge.
- Do NOT change task execution behavior.
- Do NOT change frontend.
- Do NOT add new providers or network dependencies.

## Acceptance criteria

- Planner returns a typed `PresentationPlan`, not raw sentence splits.
- Slide count is explicitly controlled and tested.
- Bullet length is bounded and tested.
- Story arc is represented explicitly.
- Existing slides generation still works via a compatibility bridge.
- Existing tests pass.

## Required tests

- planner determinism
- bounded bullet length
- min/max slide count policy
- typed slide sequence validity
- compatibility test: plan -> current renderer still yields valid PPTX

## Stop conditions

- If layout/render changes are needed beyond a compatibility bridge, stop and leave them for M10.
- If image/media placement becomes necessary, stop and leave them for M11/M12.

---

# M10 — Layout/template engine

## Goal

Add a real layout/template engine between presentation planning and PPTX rendering.

## Scope

Add:
- `SlideLayoutSpec` model
- template/theme registry
- layout resolver
- typography/spacing rules
- branded template selection
- renderer refactor to consume typed layout specs

## Minimum layout set

- title_slide
- section_slide
- title_and_bullets
- two_column_comparison
- timeline
- data_summary
- conclusion

## Allowed changes

- layout models
- template registry
- theme/template selection
- layout resolver
- renderer refactor
- focused tests

## Likely files

- `backend/app/services/slides_service/generator.py`
- `backend/app/services/slides_service/service.py`
- `backend/app/services/slides_service/templates/`
- new layout/template modules
- slides tests

## Adjacent issue firewall

- M10 assumes M9 typed planning exists.
- M10 must NOT redesign M9 planning models without necessity.
- M10 must NOT add media/image embedding. That belongs to M11.
- M10 must NOT add image generation or retrieval. That belongs to M12.
- M10 must NOT add chart/table rendering beyond layout placeholders. Full rendering belongs to M13.
- M10 must NOT add source-aware visual grounding. That belongs to M14.
- M10 must NOT add revision/update flow. That belongs to M15.

## Hard anti-scope

- Do NOT leave rendering as a single implicit layout with renamed helpers.
- Do NOT hardcode all layout behavior in one giant generator function.
- Do NOT add image placeholders that pretend to work without media embedding.
- Do NOT change task execution behavior.
- Do NOT change frontend.
- Do NOT introduce public-internet dependencies.

## Acceptance criteria

- Slide type affects layout selection.
- The same plan can render with different templates/themes.
- Typography and spacing rules are explicit and testable.
- Current default rendering remains supported.
- Generated PPTX remains valid.

## Required tests

- layout resolver tests
- template registry tests
- rendering tests for multiple layout kinds
- branded template selection tests
- PPTX validity tests

## Stop conditions

- If media assets are required for layout correctness, stop and leave them for M11.
- If chart/table blocks become necessary, stop and leave them for M13.

---

# M11 — PPTX media embedding foundation

## Goal

Add real PPTX media embedding without image generation logic.

## Scope

Add:
- media asset model for slides
- `ppt/media/*` writing
- OOXML image relationships
- picture shape rendering
- image placeholder support
- sizing/cropping/fit rules

## Allowed changes

- media model
- generator/media OOXML support
- picture rendering
- focused tests

## Likely files

- `backend/app/services/slides_service/generator.py`
- new media model/renderer modules under `backend/app/services/slides_service/`
- `backend/tests/services/test_slides_service.py`
- new media embedding tests

## Adjacent issue firewall

- M11 must NOT generate images. That belongs to M12.
- M11 must NOT retrieve images from internet or external services. That belongs to M12 if supported.
- M11 must NOT redesign planning or layout foundations.
- M11 must NOT add table/chart rendering. That belongs to M13.
- M11 must NOT add source-aware visual grounding. That belongs to M14.
- M11 must NOT add revision/update flow. That belongs to M15.

## Hard anti-scope

- Do NOT fake image embedding with empty placeholders or text boxes pretending to be images.
- Do NOT write invalid PPTX media relationships.
- Do NOT require public internet.
- Do NOT alter task execution behavior.
- Do NOT change frontend.

## Acceptance criteria

- Generator can embed image binaries into PPTX.
- `ppt/media` assets and relationships are valid.
- Picture shapes render without breaking text-only decks.
- Fit/crop rules are deterministic and tested.
- No fake media success path exists.

## Required tests

- media OOXML structure tests
- valid relationship tests
- picture shape presence tests
- fit/crop rule tests
- backward compatibility: text-only deck still valid

## Stop conditions

- If image selection/generation is needed, stop and leave it for M12.
- If charts/tables are needed as media-like blocks, leave them for M13.

---

# M12 — Image pipeline for slides

## Goal

Add image pipeline for slides: visual intent detection, image specs, provider abstraction, honest image storage, and integration with media embedding.

## Scope

Add:
- visual intent detection in planner
- `ImageSpec` model
- image provider abstraction
- generated/retrieved image storage registration
- integration with M11 media embedding
- caption/source support for images

## Minimum visual intents

- none
- cover_illustration
- hero_image
- comparison_visual
- process_visual
- product_mock

## Allowed changes

- planner image intent logic
- image models
- provider abstraction
- storage/provenance registration for images
- slides integration
- focused tests

## Likely files

- `backend/app/services/slides_service/`
- `backend/app/domain/metadata/models.py`
- `backend/app/repositories/`
- slides/service tests
- API tests only if contract extension is necessary and non-breaking

## Adjacent issue firewall

- M12 assumes M11 media embedding exists.
- M12 must NOT hardcode a specific public internet image provider.
- M12 must NOT require public internet.
- M12 must NOT redesign layout or media embedding foundations.
- M12 must NOT add full table/chart rendering. That belongs to M13.
- M12 must NOT add full source-aware visual grounding beyond minimal honest image provenance. Rich grounding belongs to M14.
- M12 must NOT add revision/update flow. That belongs to M15.

## Hard anti-scope

- Do NOT pretend images were generated if provider execution failed.
- Do NOT silently omit required images while claiming a fully visualized deck.
- Do NOT log secrets or provider tokens.
- Do NOT change frontend.
- Do NOT introduce public-internet dependency into offline intranet deployment.

## Acceptance criteria

- Planner can declare where images are needed.
- Image assets are represented explicitly, not implicitly.
- Generated/retrieved images are stored and referenced honestly.
- Slides can embed real image assets through the M11 path.
- Failure to generate/retrieve image is explicit and does not fake full success.

## Required tests

- visual intent detection tests
- image spec tests
- provider abstraction tests
- stored image metadata/provenance tests
- slide render tests with real image embedding

## Stop conditions

- If chart/table rendering is required to complete the deck, leave it for M13.
- If source-grounded image provenance is required, leave richer grounding for M14.

---

# M13 — Tables, charts, and business slide blocks

## Goal

Add structured tables, charts, and business slide blocks so decks are not limited to text cards.

## Scope

Add:
- structured slide block model
- table blocks
- chart blocks
- data-to-slide formatting
- comparison/timeline/business layouts
- optional speaker notes / appendix foundation if directly needed

## Minimum structured blocks

- text_block
- bullet_block
- table_block
- chart_block
- comparison_block
- timeline_block

## Allowed changes

- slides block models
- table/chart rendering
- business layouts
- focused tests

## Likely files

- `backend/app/services/slides_service/`
- `backend/app/services/data_service/` integration points if directly needed
- slides tests

## Adjacent issue firewall

- M13 must NOT redesign planning, layout, media, or image foundations.
- M13 must NOT require external chart services.
- M13 must NOT add full source-aware grounding. That belongs to M14.
- M13 must NOT add revision/update flow. That belongs to M15.
- M13 must NOT change frontend.

## Hard anti-scope

- Do NOT simulate tables/charts as plain bullets and claim structured rendering exists.
- Do NOT invent a full BI platform.
- Do NOT require public internet.
- Do NOT alter task execution behavior.
- Do NOT fake data-slide success when structured rendering failed.

## Acceptance criteria

- Data slides can render as tables or charts.
- Comparison/timeline layouts are explicit and tested.
- Business layouts are not simulated by plain bullets.
- PPTX remains valid and readable.
- Existing text-only deck behavior remains compatible.

## Required tests

- table rendering tests
- chart rendering tests
- timeline/comparison layout tests
- appendix/speaker note foundation tests if implemented
- PPTX validity tests

## Stop conditions

- If source-grounded citations/notes are needed for structured blocks, leave them for M14.
- If partial slide updates are needed, leave them for M15.

---

# M14 — Source-aware visual grounding

## Goal

Add source-aware visual grounding for slides: source-to-slide mapping, citations/notes, and reuse of derived_contents for planning.

## Scope

Add:
- source-to-slide mapping model
- slide citation / note model
- reuse of `derived_contents` for slide planning
- extracted figure/table candidate reuse where honest
- source-aware planner integration

## Allowed changes

- slides/source-grounding models
- planning integration
- derived-content reuse
- focused tests

## Likely files

- `backend/app/services/task_source_service.py`
- `backend/app/domain/metadata/models.py`
- `backend/app/repositories/`
- `backend/app/services/slides_service/`
- binary extraction / derived content integration tests

## Adjacent issue firewall

- M14 must NOT redesign M8 extraction foundations.
- M14 must NOT add OCR.
- M14 must NOT fake figure extraction for unsupported formats.
- M14 must NOT redesign image/media/template engines.
- M14 must NOT add deck revision/update flow. That belongs to M15.
- M14 must NOT change frontend.

## Hard anti-scope

- Do NOT bypass `derived_contents` cache.
- Do NOT claim unsupported figure/table candidate extraction works.
- Do NOT weaken existing prompt-only or text-source behaviors.
- Do NOT add public-internet dependencies.
- Do NOT alter task execution behavior.

## Acceptance criteria

- Slides/plans can reference concrete source fragments.
- Citations/notes can be attached to slides honestly.
- `derived_contents` is reused instead of re-extracting blindly.
- Extracted table/figure candidates are only used where supported.
- Unsupported visual grounding fails clearly.

## Required tests

- source-to-slide mapping tests
- citation/note tests
- derived_contents reuse tests
- supported vs unsupported candidate extraction tests
- regression tests for existing text-source flows

## Stop conditions

- If updating existing decks becomes necessary, leave it for M15.
- If unsupported figure extraction would require OCR, stop.

---

# M15 — Deck editing and revision flow

## Goal

Add deck editing and revision flow so slides are not a one-shot generator only.

## Scope

Add:
- persistent deck/revision model
- partial slide/section regeneration
- template-preserving update path
- deck versioning
- diff-aware regeneration

## Minimum revision operations

- regenerate one slide
- regenerate one section
- preserve template/theme
- create new deck revision
- inspect revision lineage

## Allowed changes

- deck/revision models
- repository support
- slides revision services
- backward-compatible API/schema changes only if required for revision contract clarity
- focused tests

## Likely files

- `backend/app/domain/metadata/models.py`
- `backend/app/repositories/`
- `backend/app/services/slides_service/`
- API routes/schemas only if revision contract is exposed
- revision tests

## Adjacent issue firewall

- M15 must NOT redesign accepted planning/layout/media/image/chart/source-grounding subsystems.
- M15 must NOT rebuild a full frontend editor UI.
- M15 must NOT alter storage truth-layer principles.
- M15 must NOT make binary files primary in Postgres.
- M15 must NOT change general task execution behavior outside revision-aware slides flow.

## Hard anti-scope

- Do NOT rebuild the entire deck blindly for every small update while claiming partial regeneration exists.
- Do NOT lose template/theme selection during revision.
- Do NOT hide revision lineage.
- Do NOT change frontend beyond explicit backward-compatible contract additions.
- Do NOT introduce public-internet dependencies.

## Acceptance criteria

- One slide or one section can be regenerated without blindly rebuilding the full deck.
- Template/theme is preserved across revisions.
- Deck revisions are stored and inspectable.
- Provenance remains revision-aware.
- Current full-deck generation still works.

## Required tests

- revision model tests
- partial regeneration tests
- template preservation tests
- version lineage tests
- backward compatibility tests for full-deck generation

## Stop conditions

- If frontend editing UX becomes necessary, stop and leave it for a later frontend phase.
- If revision support would require architectural redesign of accepted metadata/storage model, stop at the smallest safe subset.
