# P9-2 Renderer/content hardening from human review

- status: `controlled_targeted_patch`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `3b39cce346a65809c7bd73cf982a73e7a347e0bb`
- Kimi-level claimed: `False`

## Purpose

P9-2 applies the first focused hardening patch from the P9-1B human review results. The patch targets deterministic fallback planning content that produced generic labels, incomplete status-deck coverage, weak comparison-table handling, and filler slides in long structured sources.

This patch keeps scope narrow: it improves source-profile-specific planning output and adds checker/test/readiness evidence. It does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, or hidden public internet runtime requirements.

## Human-review findings addressed

P9-2 directly addresses these P9-1B findings:

- generic fallback labels such as `K1 Plan`, `Key point`, and `Additional source-grounded planning point`;
- comparison table sources being treated as plain text instead of decision matrices;
- project-log status decks stopping too early and omitting K4, K5, K6, closure, risks, and next action;
- long structured sources producing late filler slides instead of source-derived review content.

## Runtime behavior

The deterministic local fallback planner now detects bounded source profiles:

- `comparison_table`;
- `project_log`;
- `long_structured_source`;
- `technical_architecture`;
- `executive_memo`;
- `general_source`.

For comparison-table sources, the fallback plan includes a decision matrix, recommended default, optional gateway path, fallback boundary, rejected default, and release constraint. For project logs, the plan explicitly covers late K-phase milestones, closure, risks, and next action. For long structured sources, the plan keeps late slides meaningful by deriving them from source sections, evidence-package needs, and claim-review guardrails.

## Safe metadata

P9-2 adds safe planner metadata flags:

- `p9_2_renderer_content_hardening_supported`;
- `generic_fallback_labels_removed`;
- `comparison_table_decision_matrix_supported`;
- `project_log_late_phase_coverage_supported`;
- `long_source_filler_slide_prevention_supported`;
- `human_review_findings_addressed_by_p9_2`.

The metadata remains safe: raw source text, raw prompt text, and secret-like values are not stored. Existing no-claim metadata remains conservative: `kimi_level_claimed_by_k1=False` and `whole_project_kimi_level_supported=False`.

## Acceptance

P9-2 is accepted only when:

- `scripts/kw_p9_2_renderer_content_hardening_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p9_2_renderer_content_hardening.py` passes;
- production readiness `--checks-only` includes the P9-2 files;
- the targeted runner passes on profile 1;
- after commit and push, the full runner and Docker smoke pass.

P9-2 does not claim whole-project Kimi-level parity. It is a targeted product-release hardening patch derived from conservative human review findings.
