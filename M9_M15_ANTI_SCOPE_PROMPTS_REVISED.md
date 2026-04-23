# M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md

This file contains self-contained Codex prompts for M9–M15.
Each prompt is copy-paste ready and explicitly reads `M9_M15_PHASE_ISSUE_PACK.md`.

---

# Prompt M9 — Presentation planning foundation

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
Do not re-litigate F–M8 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, task-source model, or accepted metadata/derived-content architecture unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M8 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M8 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/outline.py
- backend/app/services/slides_service/service.py
- backend/app/services/slides_service/entrypoint.py
- backend/app/services/slides_service/generator.py
- backend/tests/services/test_slides_service.py

Implement M9 only.

Issue scope:
Replace primitive sentence-split slide outlining with a typed presentation planning foundation.

Allowed changes:
- PresentationPlan model
- PlannedSlide model
- slide type enum or equivalent
- deck planner service
- story arc policies
- slide-count policies
- bullet-length policies
- compatibility bridge from plan -> current renderer input
- focused tests

Required minimum slide types:
- title
- section
- content
- comparison
- timeline
- data
- conclusion
- appendix

Adjacent issue firewall:
- M9 may introduce typed planning models and planner logic.
- M9 must NOT introduce the full layout/template engine. That belongs to M10.
- M9 must NOT add media/image embedding. That belongs to M11.
- M9 must NOT add image generation or retrieval. That belongs to M12.
- M9 must NOT add tables/charts rendering. That belongs to M13.
- M9 must NOT add source-aware visual grounding. That belongs to M14.
- M9 must NOT add revision/update flow. That belongs to M15.

Hard anti-scope:
- Do NOT leave planning as sentence splitting with renamed functions.
- Do NOT hide primitive outline behavior behind a new model name only.
- Do NOT remove deterministic behavior unless replaced with bounded deterministic planning.
- Do NOT change current slides generation behavior except through a compatibility bridge.
- Do NOT change task execution behavior.
- Do NOT change frontend.
- Do NOT add new providers or network dependencies.

Acceptance criteria:
- Planner returns a typed presentation plan, not raw sentence splits.
- Slide count is explicitly controlled and tested.
- Bullet length is bounded and tested.
- Story arc is represented explicitly.
- Existing slides generation still works via a compatibility bridge.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M10 — Layout/template engine

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
M9 is accepted.
Do not re-litigate accepted F–M9 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, slides planning model, or accepted metadata architecture unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M9 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M9 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/
- backend/tests/services/test_slides_service.py
- all M9-added planning files

Implement M10 only.

Issue scope:
Add a real layout/template engine between presentation planning and PPTX rendering.

Allowed changes:
- SlideLayoutSpec model
- template registry
- theme/template selection
- layout resolver
- typography/spacing rules
- renderer refactor to consume typed layouts
- branded template selection
- focused tests

Required minimum layout types:
- title_slide
- section_slide
- title_and_bullets
- two_column_comparison
- timeline
- data_summary
- conclusion

Adjacent issue firewall:
- M10 assumes M9 typed planning exists.
- M10 must NOT redesign M9 planning models without necessity.
- M10 must NOT add media/image embedding. That belongs to M11.
- M10 must NOT add image generation or retrieval. That belongs to M12.
- M10 must NOT add chart/table rendering beyond layout placeholders. Full rendering belongs to M13.
- M10 must NOT add source-aware visual grounding. That belongs to M14.
- M10 must NOT add revision/update flow. That belongs to M15.

Hard anti-scope:
- Do NOT leave rendering as a single implicit layout with renamed helpers.
- Do NOT hardcode all layout behavior in one giant generator function.
- Do NOT add image placeholders that pretend to work without media embedding.
- Do NOT change task execution behavior.
- Do NOT change frontend.
- Do NOT introduce public-internet dependencies.

Acceptance criteria:
- Slide type affects layout selection.
- Same plan can render with different templates/themes.
- Typography and spacing rules are explicit and testable.
- Current default rendering remains supported.
- Generated PPTX remains valid.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M11 — PPTX media embedding foundation

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
M9 and M10 are accepted.
Do not re-litigate accepted F–M10 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, slides planning model, or layout/template engine unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M10 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M10 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/
- all M9/M10-added slides planning/layout files
- backend/tests/services/test_slides_service.py

Implement M11 only.

Issue scope:
Add real PPTX media embedding foundation without image generation logic.

Allowed changes:
- media asset model for slides
- ppt/media/* writing
- OOXML image relationships
- picture shape rendering
- image placeholder support
- sizing/cropping/fit rules
- focused tests

Adjacent issue firewall:
- M11 must NOT generate images. That belongs to M12.
- M11 must NOT retrieve images from internet or external services. That belongs to M12 if supported.
- M11 must NOT redesign planning or layout foundations.
- M11 must NOT add table/chart rendering. That belongs to M13.
- M11 must NOT add source-aware visual grounding. That belongs to M14.
- M11 must NOT add revision/update flow. That belongs to M15.

Hard anti-scope:
- Do NOT fake image embedding with empty placeholders or text boxes pretending to be images.
- Do NOT write invalid PPTX media relationships.
- Do NOT require public internet.
- Do NOT alter task execution behavior.
- Do NOT change frontend.

Acceptance criteria:
- Generator can embed image binaries into PPTX.
- ppt/media assets and relationships are valid.
- Picture shapes render without breaking text-only decks.
- Fit/crop rules are deterministic and tested.
- No fake media success path exists.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M12 — Image pipeline for slides

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
M9, M10, and M11 are accepted.
Do not re-litigate accepted F–M11 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, slides planning model, layout/template engine, or media embedding foundation unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M11 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M11 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/
- backend/app/domain/metadata/models.py
- backend/app/repositories/
- all M9/M10/M11 slides files

Implement M12 only.

Issue scope:
Add image pipeline for slides: visual intent detection, image specs, provider abstraction, honest image storage, and integration with media embedding.

Allowed changes:
- visual intent detection in planner
- ImageSpec model
- image provider abstraction
- generated/retrieved image storage registration
- integration with M11 media embedding
- caption/source support for images
- focused tests

Minimum visual intents:
- none
- cover_illustration
- hero_image
- comparison_visual
- process_visual
- product_mock

Adjacent issue firewall:
- M12 assumes M11 media embedding exists.
- M12 must NOT hardcode a specific public internet image provider.
- M12 must NOT require public internet.
- M12 must NOT redesign layout or media embedding foundations.
- M12 must NOT add full table/chart rendering. That belongs to M13.
- M12 must NOT add source-aware visual grounding beyond minimal honest image provenance. Rich grounding belongs to M14.
- M12 must NOT add revision/update flow. That belongs to M15.

Hard anti-scope:
- Do NOT pretend images were generated if provider execution failed.
- Do NOT silently omit required images while claiming a fully visualized deck.
- Do NOT log secrets or provider tokens.
- Do NOT change frontend.
- Do NOT introduce public-internet dependency into offline intranet deployment.

Acceptance criteria:
- Planner can declare where images are needed.
- Image assets are represented explicitly, not implicitly.
- Generated/retrieved images are stored and referenced honestly.
- Slides can embed real image assets through M11 path.
- Failure to generate/retrieve image is explicit and does not fake full success.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M13 — Tables, charts, and business slide blocks

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
M9, M10, M11, and M12 are accepted.
Do not re-litigate accepted F–M12 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, slides planning model, layout/template engine, media embedding foundation, or image pipeline unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M12 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M12 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/slides_service/
- backend/app/services/data_service/
- all M9–M12 slides files

Implement M13 only.

Issue scope:
Add structured tables, charts, and business slide blocks so decks are not limited to text cards.

Allowed changes:
- structured slide block model
- table blocks
- chart blocks
- data-to-slide formatting
- comparison/timeline/business layouts
- optional speaker notes / appendix foundation if directly needed
- focused tests

Minimum structured blocks:
- text_block
- bullet_block
- table_block
- chart_block
- comparison_block
- timeline_block

Adjacent issue firewall:
- M13 must NOT redesign planning, layout, media, or image foundations.
- M13 must NOT require external chart services.
- M13 must NOT add full source-aware grounding. That belongs to M14.
- M13 must NOT add revision/update flow. That belongs to M15.
- M13 must NOT change frontend.

Hard anti-scope:
- Do NOT simulate tables/charts as plain bullets and claim structured rendering exists.
- Do NOT invent a full BI platform.
- Do NOT require public internet.
- Do NOT alter task execution behavior.
- Do NOT fake data-slide success when structured rendering failed.

Acceptance criteria:
- Data slides can render as tables or charts.
- Comparison/timeline layouts are explicit and tested.
- Business layouts are not simulated by plain bullets.
- PPTX remains valid and readable.
- Existing text-only deck behavior remains compatible.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M14 — Source-aware visual grounding

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
M9, M10, M11, M12, and M13 are accepted.
Do not re-litigate accepted F–M13 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, source extraction model, slides planning model, layout/template engine, media foundation, image pipeline, or structured slide blocks unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M13 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M13 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/task_source_service.py
- backend/app/domain/metadata/models.py
- backend/app/repositories/
- backend/app/services/slides_service/
- all M8 source extraction files
- all M9–M13 slides files

Implement M14 only.

Issue scope:
Add source-aware visual grounding for slides: source-to-slide mapping, citations/notes, and reuse of derived_contents for planning.

Allowed changes:
- source-to-slide mapping model
- slide citation / note model
- reuse of derived_contents for slide planning
- extracted figure/table candidate reuse where honest
- source-aware planner integration
- focused tests

Adjacent issue firewall:
- M14 must NOT redesign M8 extraction foundations.
- M14 must NOT add OCR.
- M14 must NOT fake figure extraction for unsupported formats.
- M14 must NOT redesign image/media/template engines.
- M14 must NOT add deck revision/update flow. That belongs to M15.
- M14 must NOT change frontend.

Hard anti-scope:
- Do NOT bypass derived_contents cache.
- Do NOT claim unsupported figure/table candidate extraction works.
- Do NOT weaken existing prompt-only or text-source behaviors.
- Do NOT add public-internet dependencies.
- Do NOT alter task execution behavior.

Acceptance criteria:
- Slides/plans can reference concrete source fragments.
- Citations/notes can be attached to slides honestly.
- derived_contents is reused instead of re-extracting blindly.
- Extracted table/figure candidates are only used where supported.
- Unsupported visual grounding fails clearly.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M15 — Deck editing and revision flow

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–M8 phases are accepted.
M9, M10, M11, M12, M13, and M14 are accepted.
Do not re-litigate accepted F–M14 architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, deployment profile, source extraction model, slides planning model, layout/template engine, media foundation, image pipeline, structured slide blocks, or source-aware grounding model unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue’s changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–M14 architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–M14 architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
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
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M9_M15_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/domain/metadata/models.py
- backend/app/repositories/
- backend/app/services/slides_service/
- all M9–M14 slides files

Implement M15 only.

Issue scope:
Add deck editing and revision flow so slides are not a one-shot generator only.

Allowed changes:
- persistent deck/revision model
- partial slide/section regeneration
- template-preserving update path
- deck versioning
- diff-aware regeneration
- focused tests
- API/schema changes only if required for revision contract clarity and kept backward compatible

Minimum revision operations:
- regenerate one slide
- regenerate one section
- preserve template/theme
- create new deck revision
- inspect revision lineage

Adjacent issue firewall:
- M15 must NOT redesign accepted planning/layout/media/image/chart/source-grounding subsystems.
- M15 must NOT rebuild a full frontend editor UI.
- M15 must NOT alter storage truth-layer principles.
- M15 must NOT make binary files primary in Postgres.
- M15 must NOT change general task execution behavior outside revision-aware slides flow.

Hard anti-scope:
- Do NOT rebuild the entire deck blindly for every small update while claiming partial regeneration exists.
- Do NOT lose template/theme selection during revision.
- Do NOT hide revision lineage.
- Do NOT change frontend beyond explicit backward-compatible contract additions.
- Do NOT introduce public-internet dependencies.

Acceptance criteria:
- One slide or one section can be regenerated without blindly rebuilding the full deck.
- Template/theme is preserved across revisions.
- Deck revisions are stored and inspectable.
- Provenance remains revision-aware.
- Current full-deck generation still works.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```
