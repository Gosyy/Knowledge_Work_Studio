# S13f — strict per-scenario JSON rerun with schema echo and repair fallback

S13f adds a stricter public_api_dev live rerun path after S13d/S13e showed that generic or partially repaired outputs are not enough for selected benchmark acceptance.

## Controls

- one scenario per request;
- exact JSON object only;
- schema echo is required;
- at least eight slide outline entries per scenario;
- every slide must include non-empty `purpose`;
- slide-level citation and render QA checks are required;
- repair fallback is syntax-only;
- human review remains pending;
- selected parity is not claimed;
- Kimi-level is not claimed;
- Server 3 local_intranet is not verified by this public_api_dev run.

## Acceptance

Patch-stage acceptance checks only contract readiness. Live execution acceptance requires 12/12 successful GigaChat responses and 12/12 strict schema-valid scenario outputs.
