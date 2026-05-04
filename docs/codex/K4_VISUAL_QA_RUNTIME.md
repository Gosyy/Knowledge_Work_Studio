# K4 Visual QA Runtime

K4 adds a controlled local visual QA runtime for rendered PPTX artifacts.

## Scope

K4 checks a locally generated PPTX package after K3 renderer-quality preparation and approved-plan rendering. The runtime extracts a safe preview model from OOXML slide parts and evaluates deterministic quality gates:

- PPTX package and slide-count consistency;
- layout bounds;
- major visual overlap;
- estimated text overflow;
- bundled-theme contrast;
- first-pass reading order;
- explicit operator review verdicts.

## Non-goals

K4 does not add:

- public API endpoints;
- DB schema migrations;
- frontend runtime changes;
- dependency version changes;
- Dockerfile or base-image changes;
- cloud LLM or cloud vision calls;
- source-to-slide provenance runtime;
- Kimi-level claims.

PDF/image preview rendering remains out of this controlled patch. K4 inspects PPTX OOXML directly so the runtime stays offline/intranet-safe and dependency-neutral.

## Runtime contract

The K4 runtime receives:

- an approved `PresentationPlan`;
- rendered PPTX bytes;
- a local template id;
- a plan snapshot id;
- a visual QA policy.

It returns:

- a pass/review/block status;
- a bounded score;
- safe slide previews with shape counts, bounds status, reading order ids, and text digests;
- safe issue records;
- operator review metadata;
- artifact checksum metadata.

Raw source text, raw prompt text, raw slide text, and sensitive values are not stored in safe metadata.

## Acceptance

K4 is accepted only when:

- `scripts/kw_k4_visual_qa_check.py --require-ready --json` reports ready;
- targeted K0-K4 tests pass;
- production readiness includes the K4 checker;
- full runner passes;
- Docker smoke passes after commit/push.

K4 remains below Kimi-level. K5 handles source-to-slide provenance and K6 handles the end-to-end Kimi-like workflow gate.
