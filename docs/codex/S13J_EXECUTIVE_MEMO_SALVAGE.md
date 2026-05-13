# S13j deterministic executive memo salvage

S13j is a narrow recovery step after the S13i live single-scenario retry left `executive_memo_to_board_deck` at `json_parse_failed` while the other eleven selected benchmark scenarios were canonical-valid.

## Scope

S13j does not call GigaChat. It takes the failed S13i live ZIP as input, extracts the raw executive memo response text, applies deterministic JSON salvage, adapts the salvaged minimal payload into the existing S13g canonical schema, and merges it with the eleven prior S13i canonical-valid outputs.

Allowed deterministic salvage actions:

- strip markdown fences if present;
- sanitize invalid control characters;
- parse original or sanitized JSON where possible;
- use `raw_decode` for first JSON value when trailing prose exists;
- insert commas only between adjacent known JSON fields where deterministic and auditable;
- balance truncated brackets when the bracket stack is unambiguous;
- truncate to the largest parseable JSON object if safe;
- use deterministic text-to-minimal-model fallback only after JSON salvage fails;
- preserve original response and raw text digests;
- write `s13j_executive_memo_salvage_manifest.json` and `s13j_merged_salvage_manifest.json`;
- mark salvage-generated fields as not model-generated.

## Non-goals and safety boundaries

S13j must not:

- call GigaChat again;
- retry all scenarios;
- discard the eleven S13i canonical-valid outputs;
- fabricate human review results;
- auto-approve scenarios;
- claim selected offline workflow parity;
- claim Kimi-level achievement;
- claim Server 3 `local_intranet` verification from public_api_dev data;
- record raw credentials.

## Expected live output

If salvage succeeds, the live S13j merged manifest should report:

- `status = ready`;
- `scenario_count = 12`;
- `reused_canonical_scenario_count = 11`;
- `salvaged_canonical_valid_scenario_count = 1`;
- `canonical_schema_valid_scenario_count_after_merge = 12`;
- `completed_human_review_results_present_by_s13j_live = false`;
- `selected_offline_workflow_parity_claim_supported_now_by_s13j_live = false`.

Human review packet export may only be considered after the S13j live ZIP proves 12/12 canonical validity. Human review itself remains pending until real completed worksheets/results are provided.
