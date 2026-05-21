# S13k human review packet export from S13j merged artifacts

S13k exports a manual human review packet from the S13j merged 12/12 canonical-valid artifact ZIP. It is intentionally narrow: it does not call GigaChat, does not rerun model generation, does not alter S13j canonical payloads, does not fill human review worksheets, and does not approve any scenario.

## Required input

S13k requires an S13j live artifact ZIP or extracted artifact directory containing:

- `s13j_merged_salvage_manifest.json` with `status=ready`.
- Twelve `*_merged_canonical_response.json` files.
- `canonical_schema_valid_scenario_count_after_merge=12`.
- `calls_gigachat_by_s13j_live=false`.
- No completed human review results, auto-approval, selected parity claim, Kimi-level claim, Server 3 local_intranet claim, or credential values.

## Exported packet

The packet includes:

- `packet_index.json`
- `scenarios/*_evidence_manifest.json`
- `worksheets/*_worksheet.json`
- `canonical_responses/*_canonical_response.json`
- `provenance/*_s13j_provenance.json`
- `reviewer_instructions.md`
- `operator_handoff_readme.md`
- `review_result_ingest_schema.json`
- `archive_manifest.json`

All worksheets are blank and remain `pending_human_review`. Required dimensions are `storyline_quality`, `source_grounding`, `layout_visual_quality`, `native_visual_editability`, `citation_usefulness`, and `operator_workflow_fit`.

## Salvage provenance requirement

The `executive_memo_to_board_deck` worksheet and provenance file must preserve S13j salvage details, including:

- fallback method: `fallback_text_to_minimal_model_adapter`
- `source_s13i_response_digest`
- `raw_response_text_digest`
- `salvage_generated_fields_are_not_model_generated=true`
- `used_text_to_minimal_model_adapter=true`

This marker is a quality warning for the reviewer, not an approval. The reviewer must verify all claims and source grounding before any decision.

## Claims that remain unsupported

S13k does not support any of the following claims by itself:

- completed human review
- selected offline workflow parity
- Kimi-level capability
- Server 3 local_intranet verification
- executive memo content quality acceptance

The next step after S13k export is real manual review and later controlled ingest of completed review results.
