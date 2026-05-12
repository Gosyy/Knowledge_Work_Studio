# KQ Phase Quality Roadmap

KQ is the product-quality phase after S13l. S-phase proved that schema, packet, salvage, review export, and review ingest machinery can be audited, but S13l also preserved the release decision as `request_rework` for all selected scenarios.

KQ intentionally stops the JSON-only loop. Every KQ checkpoint must either produce or validate visible deck artifacts that can be opened, rendered, inspected, and reviewed.

## Non-goals

- Do not claim Kimi-level.
- Do not claim selected offline workflow parity without completed human review over real decks.
- Do not claim Server 3 local_intranet verification from public_api_dev or artifact-only checks.
- Do not fabricate human review results.
- Do not accept canonical JSON as a presentation-quality artifact.

## KQ-1 vertical slice

Focus scenario: `executive_memo_to_board_deck`.

The KQ-1 vertical slice moves from canonical schema outputs to real deck evidence:

1. **KQ-1A deck artifact quality harness**: fail fast unless a bundle contains PPTX, rendered slide screenshots, geometry/overflow QA, visual QA, citation manifest, source evidence manifest, and review packet over actual deck artifacts.
2. **KQ-1B actual PPTX generation**: generate a real executive memo board deck artifact from source evidence.
3. **KQ-1C render screenshots and visual QA repair loop**: render the deck and automatically detect layout defects before review.
4. **KQ-1D source-grounded citation manifest**: ensure every major claim is connected to bounded source evidence.
5. **KQ-1E human review packet over rendered deck**: review actual PPTX/screenshots, not JSON-only payloads.

## KQ acceptance style

A KQ checkpoint is only meaningful if it changes the quality feedback loop. It should add a real artifact, a real artifact validator, or a real repair mechanism. Metadata-only stages should be avoided unless they protect a concrete deck-quality gate.

## KQ-1B — actual executive memo PPTX generation

KQ-1B adds the first deterministic artifact-generation vertical slice for `executive_memo_to_board_deck`. It must generate a real PPTX plus rendered preview screenshots, geometry QA, visual QA, citation manifest, source evidence manifest, and review packet over actual deck artifacts. The output must pass KQ-1A. KQ-1B still does not claim Kimi-level quality, parity, or Server 3 verification, and independent Office/LibreOffice render QA is deferred to KQ-1C.
