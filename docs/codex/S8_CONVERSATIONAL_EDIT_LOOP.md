# S8 — Conversational edit loop

- status: `controlled_conversational_edit_loop_contract`
- branch: `9_Product_Release_Hardening`
- baseline before S8: `16887ec2c764f5bc149802357682ae381e7885fe`
- Kimi-level claimed: `False`

## Purpose

S8 adds the controlled conversational edit loop for Kimi Slides-class workflows under offline/intranet constraints.

The operator can ask for edits such as shortening a deck, reframing it for a board audience, adding a risk slide, replacing a table with a decision matrix, revising slide order, tightening citations, or converting a plan into an architecture-review deck.

## Contract

S8 edits must run over an existing saved plan snapshot. They must not regenerate from hidden transient prompts.

Required inputs:

- saved plan snapshot id;
- approved plan digest;
- operator edit instruction;
- citation manifest id.

Required controls:

- plan patch preview before generation;
- explicit operator approval before revised generation;
- citation manifest preservation and revalidation;
- native visual and image-region citation recheck;
- safe task event trail;
- retry/undo from previous saved plan snapshot.

## Supported edit intents

- `shorten_deck`
- `reframe_for_board`
- `add_risk_slide`
- `replace_table_with_decision_matrix`
- `revise_slide_order`
- `tighten_citations`
- `convert_to_architecture_review`

## Offline and provenance boundary

S8 uses only saved plans and existing offline/intranet evidence. It does not add hidden public web lookups, cloud search, cloud vision, or unattributed model memory.

The default production target remains offline/intranet. S8 does not verify Server 3 `local_intranet`; it only preserves the existing topology boundary.

## Acceptance

S8 is accepted when:

- S1 through S7 checkers remain ready;
- `kw_s8_conversational_edit_loop_check.py --require-ready` reports ready;
- S8 targeted smoke tests pass;
- production readiness `--checks-only` passes;
- full runner and Docker smoke pass after commit and push.
