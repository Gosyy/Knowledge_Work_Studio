# KQ-1B Executive Memo Actual PPTX Generation

KQ-1B starts the quality phase's first real artifact-generation vertical slice for `executive_memo_to_board_deck`.

## Purpose

KQ-1B is intentionally not another JSON-only review packet. It generates a deterministic, source-grounded board-deck artifact bundle containing:

- `deck/executive_memo_to_board_deck.pptx`
- rendered slide preview PNGs
- `geometry_report.json`
- `visual_qa_report.json`
- `citation_manifest.json`
- `source_evidence_manifest.json`
- `review_packet.json`
- `kq1b_generation_manifest.json`

The generated bundle must pass the KQ-1A deck artifact quality harness before it is considered review-ready.

## Claim boundaries

KQ-1B does not call GigaChat, does not rerun model generation, does not modify canonical S13 payloads, and does not fabricate human review. It also does not claim Kimi-level quality, selected offline workflow parity, or Server 3 local_intranet verification.

KQ-1B produces deterministic preview screenshots from the same slide specs used to generate the PPTX. This is useful for first-pass artifact review, but it is not an independent Office/LibreOffice render. KQ-1C should add independent PPTX render QA and screenshot comparison.

## Acceptance

KQ-1B targeted acceptance requires:

1. static KQ-1B capability check is ready;
2. smoke tests pass;
3. a generated executive memo deck bundle exists;
4. the bundle passes KQ-1A validation;
5. the bundle ZIP and quality report ZIP are valid archives;
6. production readiness checks-only passes.

Full patch-stage acceptance still requires commit, empty verdict commit, push, full runner, and Docker smoke.
