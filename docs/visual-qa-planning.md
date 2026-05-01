# S10 visual QA planning contract

S10 defines an optional multimodal / visual QA planning layer for KW Studio.
It is deliberately a contract and diagnostics step, not a visual runtime implementation.

## Scope

S10 may describe visual QA plans for generated artifacts such as PPTX/PDF outputs and browser evidence bundles.
The plan stores artifact references, expected checks, safe event references, and provenance links.

## Non-goals

- No OCR runtime is introduced in S10.
- No vision model runtime is introduced in S10.
- No cloud visual API or internet dependency is introduced in S10.
- No raw screenshots, raw pixels, raw DOM, raw HTML, raw OCR text, cookies, tokens, or API keys may be stored in the visual QA plan payload.
- No autonomous browser expansion is introduced in S10.

## Runtime topology

Future visual QA runtime may be implemented later as an optional Server 2 heavy-node module.
Server 1 continues to run KW Studio core services.
Server 3 continues to host local GigaChat as the default production LLM.

## Required S10 controls

- `offline_ready=true`
- `runtime_scope=contract_only_no_multimodal_runtime`
- `visual_runtime_required=false`
- `external_model_allowed=false`
- `internet_required=false`
- `server_2_heavy_runtime_optional=true`
- artifact references only; no raw visual payloads
- operator review required for planned checks
- provenance link required for artifact history

## Required checks

- artifact integrity
- source-to-artifact provenance
- layout consistency risk
- text overflow risk
- reading order risk
- contrast risk

## Validation

```bash
python3 scripts/kw_visual_qa_planning_check.py --repo-root . --mode slides --require-ready
python3 scripts/kw_visual_qa_planning_check.py --repo-root . --mode artifact --require-ready
python3 -m pytest backend/tests/smoke/test_s10_visual_qa_planning_contract.py -q
```
