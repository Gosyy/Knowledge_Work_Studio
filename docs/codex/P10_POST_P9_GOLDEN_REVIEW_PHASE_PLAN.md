# P10 Post-P9 golden benchmark regeneration and human re-review plan

- status: `controlled_phase_start`
- branch: `9_Product_Release_Hardening`
- baseline before phase: `42d999a93a6328c1f35e8e3118b6bca6ab3f45ca`
- Kimi-level claimed: `False`

## Purpose

P10 starts after the closed P9 product-release hardening evidence track. P9 captured human-review findings, applied focused content/layout/visual-QA/provenance/semantic-coverage hardening, produced review-readiness evidence, and closed with known non-blocking warning classification.

P10 is the validation phase that checks whether the P9 hardening actually improved the golden benchmark artifacts for a human reviewer. It must regenerate or re-open post-P9 artifacts, compare them against the original P9-1B findings, and perform a new human re-review before changing any approval state.

## P10-1 - Post-P9 regeneration readiness

P10-1 is intentionally evidence-only. It does not regenerate PPTX artifacts by itself. It verifies that the repository contains the accepted P9 closure chain, the original five P9-1B `request_rework` golden cases, and the RC1 golden benchmark harness needed to produce a post-P9 artifact pack.

The output of P10-1 is a deterministic regeneration plan:

- five golden benchmark case IDs to regenerate;
- expected artifact triplets per case: PPTX, manifest, safe metadata;
- preserved original P9-1B decisions, all still `request_rework` until re-review;
- explicit requirement for future human re-review;
- known non-blocking warning classification inherited from P9-7/P9-8;
- no Kimi-level claim.

## Next P10 steps

The intended follow-up sequence is:

1. `P10-2` - generate a post-P9 golden benchmark artifact pack using the accepted local/offline harness.
2. `P10-3` - compare the post-P9 artifacts against the original P9-1B findings.
3. `P10-4` - run or capture a new human re-review using the existing rubric.
4. `P10-5` - create a release decision dossier from the new review results.
5. Targeted fixes only if the new human review still finds blockers.


## P10-2 - Post-P9 golden artifact pack generation

P10-2 starts from accepted P10-1 on branch `9_Product_Release_Hardening` at `2bc43dad0a55011c8627841b6fd5e2cc7be12f09`. It runs the accepted local/offline RC1/K6 golden benchmark harness to generate a post-P9 artifact pack for the same five golden cases.

The patch verifies one PPTX, one manifest, and one safe metadata file per case, plus a P10-2 artifact pack manifest. It does not approve any deck, does not change the original P9-1B review decisions, and does not claim Kimi-level parity. Human re-review remains required before any approval-state change.

P10-2 is registered in the production readiness executable gate as an artifact-pack generation checkpoint. The production gate uses a temporary artifact directory, while operators can pass `--artifacts-dir` to persist the pack for P10-3/P10-4.

## Scope guard

P10-1 does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud LLM, cloud vision, public-internet runtime requirements, or Kimi-level claims.

P10-1 does not run `npm audit fix --force`, does not change package versions, and does not remediate dependency/security warnings. Those remain a separate controlled track.

## Acceptance

P10-1 is accepted only when:

- `scripts/kw_p10_1_post_p9_regeneration_readiness_check.py --repo-root . --require-ready --json` reports `ready`;
- `backend/tests/smoke/test_p10_1_post_p9_regeneration_readiness.py` passes;
- P9-8 closure evidence remains present;
- production readiness `--checks-only` includes the P10-1 files;
- after commit and push, the full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.

## Production readiness gate integration

P10-1 is registered in the production readiness executable gate as an evidence-only checkpoint. The gate runs `scripts/kw_p10_1_post_p9_regeneration_readiness_check.py --require-ready --json` after the P9 closure checks so the start of the post-P9 regeneration phase is visible in full-runner logs rather than only in targeted runner logs.

This integration does not generate artifacts, does not change approval state, does not run `npm audit fix --force`, does not change dependency versions, and does not claim Kimi-level parity.

## P10-3 - Post-P9 artifact comparison report

P10-3 starts from accepted P10-2 on branch `9_Product_Release_Hardening` at `048443a073b807026a2de725e1d069f60a7e6a18`. It compares the regenerated post-P9 golden artifact pack against the original P9-1B human-review findings.

The patch produces deterministic comparison cards for the same five golden benchmark cases. Each card preserves the original `request_rework` decision, original blocker/warning counts, regenerated artifact evidence, manifest/safe metadata availability, and the requirement for future human re-review.

P10-3 does not approve any deck, does not change the original P9-1B review decisions, and does not claim Kimi-level parity. It is a comparison/evidence checkpoint that prepares inputs for P10-4 human re-review.

## P10-4 - Post-P9 human re-review capture workflow

P10-4 starts from accepted P10-3 on branch `9_Product_Release_Hardening` at `c854830ae885ffdde80da6a3de6c0f7466433bd2`. It converts the P10-3 comparison report into a deterministic human re-review packet for the same five golden benchmark cases.

The patch generates one review worksheet per case using the existing human-review rubric, original P9-1B findings, and regenerated post-P9 artifact evidence. Each worksheet keeps the post-P9 decision state as `pending_human_review` and requires an operator to enter reviewer ID, timestamp, decision, scores, slide findings, and follow-up backlog.

P10-4 does not approve any deck, does not reject any deck, does not change the original P9-1B review decisions, and does not claim Kimi-level parity. It is a capture workflow that prepares inputs for P10-5 only after a real human review has been completed.

## P10-5a - GigaChat API golden benchmark execution

P10-5a starts from accepted P10-4 on branch `9_Product_Release_Hardening` at `0e29e74b3f275d9c3fbfbd517ff212bf62c88c56`. It runs the five golden benchmark cases through the real GigaChat public API development route before the P10-5 release decision dossier.

The checkpoint is deliberately named `P10-5a` rather than `strict local GigaChat` because this run uses the internet/key-based GigaChat API route, not the production Server 3 local intranet route. It is real provider evidence, but it does not verify the offline/intranet topology.

P10-5a forbids silent deterministic fallback in live mode: all five cases must use GigaChat output, and the RC3 comparison status must be `compared_local_gigachat_to_fallback`. It does not change approval state, does not auto-approve generated decks, and does not claim Kimi-level parity.

## P10-5 - Release decision dossier

P10-5 starts from accepted P10-5a on branch `9_Product_Release_Hardening` at `157776bc14cb759c4a8b2bd3453d41f6c02dde52`. It creates a release decision dossier from the post-P9 regeneration, comparison, human re-review capture workflow, and GigaChat API benchmark evidence chain.

Because the P10-4 human re-review worksheets remain pending until a real reviewer fills them in, P10-5 does not approve or reject the release. The supported decision is `defer_pending_human_re_review`, with `release_approval_granted_by_p10_5 = false`.

P10-5 also preserves the P10-5a boundary: public API GigaChat evidence is real provider evidence, but it is not proof of the production Server 3 offline/intranet route. P10-5 does not claim Kimi-level parity and does not change API, DB, frontend, dependency, Docker, or cloud-production runtime scope.\n\n## P10-6 - Human review packet export

P10-6 starts from accepted P10-5 on branch `9_Product_Release_Hardening` at `6ab666e845898731d27e0b109b722c2eace70787`. It exports a persistent human-review packet from the accepted P10 evidence chain.

The packet bundles regenerated post-P9 artifact evidence, P10-3 comparison cards, and P10-4 pending review worksheets so a human reviewer can complete the five golden-case decisions. It does not complete the review, does not change approval state, and does not claim Kimi-level parity.

P10-6 keeps the release decision deferred as `defer_pending_human_re_review` until P10-7 ingests completed human-review results. P10-5a public API GigaChat evidence remains explicitly separated from production Server 3 offline/intranet proof.\n

## P10-7a - Human review worksheet import validator

P10-7a starts from accepted P10-6 on branch `9_Product_Release_Hardening` at `8c5b08bb11ac847fd5a165782f68081029ef43c5`. It adds a conservative validator for real completed human-review worksheet payloads before any P10-7 ingest step.

The checkpoint validates reviewer identity, review timestamp, decision, review-dimension scores, slide-level findings, and follow-up backlog for the same five golden benchmark cases. It rejects pending worksheets, missing cases, unknown cases, approval-state changes, Kimi-level claims, auto-approval flags, and Server 3 offline/intranet proof claims embedded in review payloads.

P10-7a is tooling only. It does not ingest completed review results, does not approve or reject the release, does not approve any deck, and does not claim Kimi-level parity. The release decision remains `defer_pending_human_re_review` until a later P10-7 ingest patch runs against real completed, validator-passing human review results.


## P10-7 - Human review results ingest

P10-7 starts from accepted P10-7a on branch `9_Product_Release_Hardening` at `0084a9fd9e0b45480c4881097b291a8855517a92`. It ingests completed P10 human-review results that passed the P10-7a worksheet import validator.

The ingested review evidence is the project-owner-accepted AI-assisted analysis of the P10-6 human-review packet. It records completed decisions for all five golden benchmark cases: four `approve`, one `request_rework`, and zero `reject`.

P10-7 does not approve the release. Because `k0_arch_doc_to_architecture_deck` remains `request_rework`, the supported post-ingest decision remains deferred as `defer_pending_review_rework` / `defer_pending_human_re_review`. P10-7 also preserves the GigaChat boundary: the project may finish on accepted `public_api_dev` GigaChat benchmark evidence, but P10-7 does not verify the production Server 3 `local_intranet` route and does not represent public API evidence as offline/intranet proof.

## P10-8 - Final release decision dossier after completed human review

P10-8 starts from accepted P10-7 on branch `9_Product_Release_Hardening` at `6bf239d5f5399923a451d93ddd5f305fc3e51f6a`. It creates the final P10 release decision dossier from completed human-review evidence.

The completed review results contain four `approve` decisions, one `request_rework`, and zero `reject` decisions. The remaining request-rework case is `k0_arch_doc_to_architecture_deck`, so P10-8 does not grant release approval and keeps the supported final decision as `defer_pending_targeted_rework`.

P10-8 records that the project completion path may rely on the accepted real GigaChat `public_api_dev` benchmark evidence, while explicitly preserving that this is not production Server 3 `local_intranet` proof. Production/offline mode remains the target deployment mode, and Server 3 local-intranet operator readiness can be prepared separately without claiming verification.

## P10-9 - Targeted architecture deck rework and re-review closure

P10-9 starts from accepted P10-8 on branch `9_Product_Release_Hardening` at `8d34eab97eb89920e9f73a19e38b3cad4190c187`. It resolves the single remaining P10-8 request-rework case, `k0_arch_doc_to_architecture_deck`, without reopening the whole golden benchmark phase.

The checkpoint hardens the technical architecture planning path so the 8-slide architecture deck uses a complete architecture-review storyline: topology map, production path, Server 2 boundary, closed foundation controls, runtime capabilities, failure modes/operator gates, and release-readiness ownership. The previous repetitive tail slides are replaced and slide 7 is guarded as `Failure modes and operator gates`.

P10-9 does not grant final release approval. It supports the next decision state `ready_for_final_release_approval_dossier` and leaves the actual approval to a separate P10-10 checkpoint. It also does not claim Kimi-level parity and does not verify Server 3 `local_intranet`; public API GigaChat evidence remains real provider evidence but not offline/intranet proof.
