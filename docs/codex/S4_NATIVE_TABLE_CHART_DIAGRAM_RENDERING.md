# S4 — Native table/chart/diagram rendering

- status: `controlled_native_visual_rendering_contract`
- branch: `9_Product_Release_Hardening`
- baseline before S4: `c75656b23b5166a4b79ded85c1968ab74ee0185c`
- Kimi-level claimed: `False`

## Purpose

S4 turns the S3 adaptive deck-mode registry into a native visual-rendering contract. It defines how KW Studio should represent tables, charts, and diagrams as editable PPTX-native elements instead of flattened screenshots or generic bullet text.

The checkpoint focuses on the benchmark-aligned modes created in S3:

- `executive_board_deck`;
- `architecture_review_deck`;
- `project_status_deck`;
- `decision_matrix_deck`;
- `long_document_explainer`.

## Native visual requirements

S4 requires three editable PPTX-native visual families:

1. `pptx_table` — editable tables for decision matrices, risk registers, failure gates, evidence packages, and owner/action rows.
2. `pptx_chart` — editable chart/scorecard/timeline views for executive signals, tradeoffs, and milestone timelines.
3. `pptx_diagram` — editable shape/connector diagrams for topology maps and document section maps.

Raster screenshots are not accepted as the primary path for these visuals.

## Mode-specific acceptance

S4 is accepted when the registry contains native visual specifications for all five S3 deck modes and explicitly covers:

- native decision option matrix rendering;
- native architecture topology diagram rendering;
- native architecture failure-mode/operator-gate table rendering;
- native project-status milestone timeline rendering;
- native long-document evidence table rendering.

Each visual specification must include a data model policy, renderer contract, layout guard, and source-to-visual provenance policy.

## Boundaries

S4 does not rewrite the PPTX renderer, add API endpoints, add DB migrations, change frontend runtime, change dependencies, change Docker files, add cloud LLM, add cloud vision, or require public internet. It is an offline/intranet-compatible rendering contract and registry.

S4 also does not claim Kimi-level parity. It prepares the next implementation steps by making the visual families explicit and testable.

## Next step

The next controlled S-phase step is `S5 — template and slide-master ingestion with local template constraints`.
