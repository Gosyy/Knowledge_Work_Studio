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

## P10-10 - Final release approval dossier

P10-10 starts from accepted P10-9 on branch `9_Product_Release_Hardening` at `405a6ea1a418ec1aa5df5648ce0dcba1da2e073d`. It creates the final release approval dossier after the targeted architecture rework resolved the only remaining P10-8 request-rework case.

The checkpoint grants release approval because all five golden benchmark cases are approved after P10-9, with zero request-rework decisions, zero rejects, and no blocking case IDs. This is not an owner-waiver path; it is based on completed review evidence plus targeted rework closure.

P10-10 preserves all release boundaries: no Kimi-level parity claim, no Server 3 `local_intranet` verification claim, no dependency/security remediation, no API/DB/frontend/Docker/cloud runtime scope changes, and no hidden public-internet production dependency. The accepted P10-5a `public_api_dev` GigaChat benchmark remains real provider evidence for the project completion path, but not production Server 3 offline/intranet proof.

## P10-11 - Final operator release closure

P10-11 starts from accepted P10-10 on branch `9_Product_Release_Hardening` at `f369412ba284f5f149a81ab42cb25b45b74bfaa4`. It closes the release workflow for operator handoff after P10-10 granted release approval.

The checkpoint records `project_release_status_after_p10_11 = approved_for_operator_handoff`, preserves profile-specific operator paths, keeps logs in `<repo>/logs`, treats Downloads as handoff-only, and records that future assistant patches must be applied and tested locally before handoff whenever technically possible.

P10-11 does not add runtime scope. It keeps all release boundaries: no Kimi-level parity claim, no Server 3 `local_intranet` verification claim, no dependency/security remediation, and no hidden public-internet production dependency.

## S1 - Kimi Slides-class gap dossier

S1 starts the S-phase Kimi Slides-class workflow quality track after P10 release closure. It defines ten controlled S-phase targets: outline-first workflow, editable plan before generation, adaptive deck modes, native table/chart/diagram rendering, template/master ingestion, image/screenshot-to-slide workflow, offline research citations, conversational edit loop, render-based visual QA, and expanded Kimi-style benchmark.

S1 is a gap dossier and roadmap checkpoint only. It does not claim Kimi-level parity and does not change runtime, API, DB, frontend, Docker, dependency, cloud LLM, or cloud vision scope. The next execution phase is S2 outline-first frontend workflow.

## S2 - Outline-first frontend workflow

S2 starts from accepted S1 on branch `9_Product_Release_Hardening` at `9bade7ea43ef8cc5db994a183d9cdb984e541ebe`. It turns the S1 outline-first gap into a controlled frontend-facing workflow contract.

The checkpoint requires the operator journey to show an outline before generation, allow editable plan review, require explicit plan approval, require adaptive/template render mode selection, generate PPTX from the approved plan, register artifact history and plan snapshots, and retry from saved plans.

S2 does not change runtime scope. It does not add API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker changes, cloud LLM, cloud vision, Kimi-level claims, or Server 3 `local_intranet` verification. It advances the Kimi Slides-class roadmap while preserving offline/intranet production boundaries.

## S3 - Adaptive deck modes

S3 starts from accepted S2 on branch `9_Product_Release_Hardening` at `fb5d888f9348c07a57b94387f0b201f38c785010`. It adds a benchmark-aligned adaptive deck mode registry for executive, architecture, status, decision-matrix, and long-document explainer decks.

The checkpoint requires mode-specific storylines, slide archetypes, table/chart policies, visual QA expectations, provenance expectations, and failure guards before later S4/S9 rendering and visual QA work. S3 does not claim Kimi-level parity, does not verify Server 3 `local_intranet`, and does not add API, DB, frontend runtime, dependency, Docker, cloud LLM, or cloud vision scope.

## S4 - Native table/chart/diagram rendering

S4 starts from accepted S3 on branch `9_Product_Release_Hardening` at `c75656b23b5166a4b79ded85c1968ab74ee0185c`. It defines an offline-safe native visual-rendering registry for editable PPTX tables, charts, and diagrams.

The checkpoint consumes the S3 adaptive deck-mode registry and adds mode-specific native visual specifications for decision matrices, architecture topology diagrams, failure-mode/operator-gate tables, project milestone timelines, risk registers, and long-document evidence packages.

S4 does not rewrite the renderer or change runtime scope. It does not add API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker changes, cloud LLM, cloud vision, public-internet production dependency, Kimi-level claims, or Server 3 local-intranet verification claims.

## S5 - Template and slide-master ingestion

S5 starts from accepted S4 on branch `9_Product_Release_Hardening` at `f04190dc56d7817401482f04b1289aa6bb2d0a6e`. It defines an offline-safe template and slide-master ingestion contract that maps local template metadata to S3 adaptive deck modes and S4 native visual specifications.

The checkpoint extracts local template master/theme/layout metadata from the bundled registry, rejects external template references, and maps deck archetypes plus native visuals to available local slide layouts.

S5 does not add API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker changes, cloud LLM, cloud vision, public-internet production dependency, Kimi-level claims, or Server 3 local-intranet verification claims.

## S6 - Image/screenshot-to-slide workflow

S6 starts from accepted S5 on branch `9_Product_Release_Hardening` at `0ce33b74473e8ffdbf6e47f4096da86b66b898eb`. It adds an offline-safe workflow contract for turning screenshots, images, and scanned page images into slide-ready structures.

The checkpoint defines local heavy-module boundaries for OCR, layout detection, region segmentation, and table-structure detection; requires source-image-to-region and region-to-slide-element provenance; and prefers editable PPTX reconstruction over raster fallback. Raster fallback is allowed only as a non-primary path with an explicit reason.

S6 does not add cloud vision, public-internet dependency, public API endpoints, DB migrations, frontend runtime changes, dependency changes, Docker changes, Kimi-level claims, or Server 3 `local_intranet` verification claims. The next execution phase is S7 offline/intranet research citations.


## S7 - Offline/intranet research citations

S7 starts from accepted S6 on branch `9_Product_Release_Hardening` at `7a0e6732429b6fc9e29e78ef49453f6715f320d3`. It adds an offline/intranet citation manifest contract for source-grounded slides.

The checkpoint requires citations for slide-level claims, S4 native PPTX tables/charts/diagrams, and S6 image/screenshot crop-region reconstructions. Allowed evidence sources are uploaded documents, internal browser evidence packets, local knowledge-base entries, intranet documents, image-region evidence, and generated artifact manifests.

S7 does not add public API endpoints, DB migrations, frontend runtime, dependency, Docker, cloud LLM, cloud vision, or hidden public-internet production requirements. It does not claim Kimi-level parity and does not verify Server 3 `local_intranet`.

## S8 - Conversational edit loop

S8 starts from accepted S7 on branch `9_Product_Release_Hardening` at `16887ec2c764f5bc149802357682ae381e7885fe`. It defines the conversational edit loop over saved plan snapshots and citation-aware deck revisions.

The checkpoint supports edit intents such as shortening a deck, reframing it for a board audience, adding risk slides, replacing tables with decision matrices, revising slide order, tightening citations, and converting an approved plan into an architecture-review deck. All edits require a saved plan snapshot, approved plan digest, operator edit instruction, citation manifest, plan patch preview, explicit operator approval, and citation revalidation before revised generation.

S8 does not add API, DB, frontend runtime, dependency, Docker, cloud LLM, or cloud vision scope. It does not allow hidden public internet or transient-prompt-only generation, does not claim Kimi-level parity, and does not verify Server 3 `local_intranet`. The next controlled phase is S9 render-based visual QA.
## S9 - Render-based visual QA

S9 starts from accepted S8 on branch `9_Product_Release_Hardening` at `79e4e71463f2a68668c039f2e9f35d6faabe7f52`. It defines render-based visual QA for actual slide screenshots and local geometry manifests.

The checkpoint requires rendered slide evidence, slide geometry manifests, native visual geometry from S4, image-region reconstruction evidence from S6, citation manifests from S7, and revised plan snapshot metadata from S8. It guards title/body collisions, text overlap, clipped text, tiny text, table overflow, dense native visuals, chart label collisions, diagram node overlap, image reconstruction mismatches, and citation marker visibility.

S9 does not add API endpoints, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, cloud vision, public internet, or Kimi-level claims. It prepares the final S10 benchmark by making visual QA evidence human-reviewable and render-grounded.

## S10 - Expanded Kimi-style benchmark and human review

S10 starts from accepted S9 on branch `9_Product_Release_Hardening` at `e2954d5e9d837571567c14b184cbc5dcebe86a7f`. It defines the expanded Kimi-style offline benchmark and human-review contract for selected workflow parity scenarios.

The checkpoint defines twelve benchmark scenarios covering executive, architecture, project-status, decision-matrix, long-document, research, KPI, product-launch, training, screenshot/image, branded-template, and browser-evidence workflows. Each scenario requires S1-S9 evidence, approved plan snapshots, generated PPTX artifacts, manifests, citations, render geometry, render-based visual QA, and real completed human review before any selected parity claim.

S10 does not claim Kimi-level parity. It only permits a future evidence-backed and scoped wording: `Kimi Slides-class offline workflow parity for selected benchmark scenarios.` S10 also does not verify Server 3 `local_intranet` and does not add API, DB, frontend runtime, dependency, Docker, cloud LLM, cloud vision, or hidden public-internet production scope.
## S11 - S-phase closure dossier

S11 starts from accepted S10 on branch `9_Product_Release_Hardening` at `c2ad133c54b872b8af69e1611464e9466016cbec`. It closes the S1-S10 capability foundation as an S-phase closure dossier.

The checkpoint records that S1-S10 are complete as controlled capability contracts and that the future selected parity wording is limited to `Kimi Slides-class offline workflow parity for selected benchmark scenarios.` S11 does not run the 12-scenario benchmark, does not fabricate human review results, and does not claim Kimi-level parity.

S11 preserves all boundaries: no Server 3 `local_intranet` verification claim, no hidden public-internet production dependency, no cloud research, no cloud vision, no API/DB/frontend/Docker/dependency scope change, and no `npm audit fix --force`.

### S12 — Selected benchmark execution packet / human review workflow

Status: targeted implementation pending full-runner closure.

S12 prepares the execution packet for the selected S10 12-scenario benchmark and human review workflow. It creates the contract for scenario execution manifests, evidence manifests, reviewer worksheets, reviewer instructions, and review-result ingest boundaries.

S12 does not execute the benchmark, does not fabricate completed human review results, does not auto-approve scenarios, and does not support the selected offline workflow parity claim until future completed benchmark results and real human review exist.

## S13a - Selected benchmark review packet skeleton

S13a prepares the review-packet skeleton for the 12 S10 selected benchmark scenarios. It does not run live GigaChat, does not perform public_api_dev execution, does not fill human review results, and does not support a selected offline workflow parity claim yet.

The initial execution state is `packet_skeleton_ready`; the initial review state remains `pending_human_review`. Real completed human review results are still required before any selected offline workflow parity claim.
## S13b — live public_api_dev GigaChat generation for 12 selected benchmark scenarios

Status: planned/controlled live-generation workflow.

S13b adds the explicit `public_api_dev` GigaChat generation path for the twelve S10 selected benchmark scenarios. The normal production readiness gate validates the static live-generation contract without requiring secrets or network access. The actual live run must be invoked separately with shell environment credentials and must never commit or log raw credential values.

S13b preserves these boundaries: public API evidence is not Server 3 `local_intranet` proof; generated artifacts do not complete human review; selected offline workflow parity is not supported until real completed human review results are ingested.
