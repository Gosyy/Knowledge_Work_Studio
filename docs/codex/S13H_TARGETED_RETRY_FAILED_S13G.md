# S13h — Targeted retry for failed S13g scenarios

S13h defines a narrow execution workflow for retrying only the failed S13g canonical adapter scenarios while preserving already canonical-valid S13g outputs.

## Scope

S13h is intentionally narrow:

- retry only failed S13g scenarios;
- reuse prior canonical-valid S13g scenario outputs;
- merge reused and retried outputs into a combined canonical packet;
- preserve model-vs-adapter provenance;
- preserve original response digests;
- record retry reason and retry source;
- keep human review pending;
- do not claim selected parity;
- do not claim Kimi-level;
- do not claim Server 3 `local_intranet` verification.

## Current known failed scenarios from S13g live run

The S13g live canonical adapter rerun produced 12 model responses, but only 10 canonical-valid scenarios. The targeted retry set is:

- `executive_memo_to_board_deck`
- `browser_evidence_packet_to_cited_deck`

Both failures were malformed JSON parse failures. S13h therefore performs a targeted live retry for those scenarios and merges them with the 10 already canonical-valid outputs.

## Required artifacts

S13h execution requires an input S13g live ZIP containing:

- `s13g_canonical_adapter_live_generation_manifest.json`;
- per-scenario `*_canonical_adapter_response.json` files;
- canonical-valid outputs for all reusable scenarios.

S13h execution produces:

- `s13h_targeted_retry_manifest.json`;
- per-scenario merged canonical response JSON files;
- retry scenario response JSON files;
- combined canonical output ZIP;
- explicit safety and provenance boundaries.

## Acceptance

S13h execution is ready only if:

- prior S13g input has 12 successful model responses;
- exactly the failed scenarios are retried unless explicitly overridden;
- all 12 scenarios are canonical-valid after merge;
- reused scenarios keep their prior canonical payload and digest;
- retried scenarios include retry provenance;
- no credential values are recorded;
- completed human review is absent;
- selected offline workflow parity is not claimed;
- Kimi-level is not claimed;
- Server 3 `local_intranet` is not claimed.

S13h is not human review and cannot approve the benchmark.
