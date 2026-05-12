# KQ-1A Deck Artifact Quality Harness

KQ-1A is the first quality-phase checkpoint after S13l. It introduces a deterministic deck artifact quality harness for the `executive_memo_to_board_deck` scenario.

## Goal

KQ-1A prevents KW Studio from treating schema-valid JSON as presentation quality. A bundle can pass KQ-1A only when it contains actual deck artifacts:

- PPTX deck file with valid OOXML structure.
- Rendered slide screenshots.
- Geometry report covering slide count, empty slides, text overflow, and tiny text.
- Visual QA report with no blocking defects.
- Citation manifest with slide-level claims and source excerpts.
- Source evidence manifest with bounded evidence items.
- Review packet that explicitly references the real deck artifacts and remains pending human review.

## Controlled scope

KQ-1A is a quality harness only. It does not generate a PPTX, call GigaChat, rerun model generation, change frontend runtime, add API endpoints, alter DB schema, change Dockerfiles, or modify dependency versions.

KQ-1A must keep these claims false:

- `kimi_level_claimed_by_kq1a`
- `whole_project_kimi_level_supported`
- `selected_offline_workflow_parity_claim_supported_after_kq1a`
- `server3_local_intranet_route_verified_by_kq1a`

## Inputs

The runtime validator accepts either a ZIP file or an extracted bundle directory.

Expected bundle layout can be flexible, but these files are recognized by name:

- `*.pptx`
- `rendered_slides/*.png`
- `geometry_report.json`
- `visual_qa_report.json`
- `citation_manifest.json`
- `source_evidence_manifest.json`
- `review_packet.json`
- optional `kq1a_deck_artifact_manifest.json`

## Failure mode that matters

A JSON-only bundle must fail. This is intentional. KQ-1A exists to stop the old loop where canonical schema validity was mistaken for deck quality.

## Downstream path

KQ-1A is a gate. The next checkpoint should be KQ-1B, which creates an actual executive memo board deck so that KQ-1A can evaluate a real generated PPTX bundle instead of only synthetic smoke fixtures.
