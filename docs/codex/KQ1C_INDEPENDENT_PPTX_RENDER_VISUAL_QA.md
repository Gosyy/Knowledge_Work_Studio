# KQ-1C Independent PPTX Render and Visual QA Loop

KQ-1C adds an independent render/QA pass over the actual `executive_memo_to_board_deck.pptx` bundle produced by KQ-1B.

## Purpose

KQ-1B generated a PPTX and deterministic preview screenshots from slide specs. That was enough to prove the product can produce an artifact bundle, but it was not enough to prove the PPTX renders cleanly outside the generator.

KQ-1C closes that gap for the first vertical slice by:

- reading the actual PPTX from a KQ-1B deck bundle;
- rendering it independently to PNG slides;
- producing `kq1c_render_manifest.json`;
- producing `kq1c_visual_qa_report.json` from the independent render output;
- updating `geometry_report.json` and `visual_qa_report.json` with KQ-1C findings;
- updating `review_packet.json` with independent render references;
- validating the enhanced bundle through KQ-1A.

## Render engines

The default `auto` mode tries LibreOffice headless PDF export plus `pdftoppm` first. When that render stack is unavailable, it falls back to a deterministic Python PPTX text renderer that reads the PPTX itself and renders extracted slide text to PNG.

The fallback is still independent of the KQ-1B preview screenshots because it reads the actual PPTX file. It is not equivalent to a full Office visual fidelity render, so the report clearly distinguishes:

- `independent_pptx_render_performed_by_kq1c`
- `independent_office_render_performed_by_kq1c`
- `render_engine`

Operators can force true Office/PDF rendering with `--require-office-render`.

## Claim boundaries

KQ-1C does not call GigaChat, does not rerun model generation, does not modify canonical S13 payloads, and does not fabricate human review. It also does not claim Kimi-level quality, selected offline workflow parity, or Server 3 local_intranet verification.

KQ-1C proves a render/QA loop exists for the actual PPTX artifact. It does not prove final visual quality, brand quality, full template fidelity, or human acceptance.

## Acceptance

KQ-1C targeted acceptance requires:

1. static KQ-1C capability check is ready;
2. smoke tests pass;
3. a KQ-1B bundle is generated or supplied;
4. KQ-1C renders the actual PPTX independently;
5. KQ-1C visual QA reports zero empty slides, zero text overflow, and zero tiny text;
6. the enhanced bundle passes KQ-1A validation;
7. enhanced bundle ZIP and quality report ZIP are valid archives;
8. production readiness checks-only passes.

Full patch-stage acceptance still requires commit, empty verdict commit, push, full runner, and Docker smoke.
