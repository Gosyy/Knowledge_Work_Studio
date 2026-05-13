# S13e — Hardened output repair/parser and validation rerun

S13e adds a deterministic repair/parser boundary for S13d hardened live GigaChat outputs.

S13e is intentionally not another model run. It consumes the failed S13d hardened rerun ZIP or an extracted S13d artifacts directory, repairs format-level defects, and revalidates the existing outputs against the S13d schema.

## Scope

S13e may:

- strip markdown code fences around JSON;
- parse the first JSON object with `JSONDecoder.raw_decode`;
- trim trailing extra text after a valid JSON object;
- normalize schema fields that the model nested under `approved_plan_candidate`;
- sanitize invalid JSON control characters when parsing otherwise fails;
- write per-scenario repaired payloads and a repair manifest.

S13e must not:

- call GigaChat again;
- change or hide the original response digest;
- fabricate human review results;
- auto-approve scenarios;
- claim selected offline workflow parity;
- claim Kimi-level achievement;
- claim Server 3 `local_intranet` verification;
- record raw credentials.

## Acceptance boundary

S13e is accepted as a workflow when the repair/parser contract is ready and covered by targeted tests. The execution export is accepted only when the repair run reports 12/12 schema-valid scenarios. If deterministic repair cannot reach 12/12, the next step is S13f: a stricter live prompt rerun.

## Claim boundary

S13e can only improve parseability and schema validation of already-generated S13d outputs. It does not produce completed human review results and does not support the selected parity claim by itself.
