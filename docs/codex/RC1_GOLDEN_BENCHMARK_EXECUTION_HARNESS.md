# RC1 — Golden benchmark execution harness

RC1 adds a release-candidate benchmark execution harness for the K0 golden cases. It is a verification/checkpoint layer, not a new product runtime capability.

## Purpose

RC1 runs the five K0 golden benchmark cases through the already accepted K6 workflow:

1. source memo to executive deck;
2. technical document to architecture deck;
3. project log to status deck;
4. comparison table to decision deck;
5. long DOCX/PDF-like source to structured presentation.

For each case, the harness executes:

```text
fixture source -> K6 workflow -> PPTX artifact -> manifest -> source-to-slide provenance -> Visual QA -> operator-gate summary
```

## Scope boundaries

RC1 does not add a public endpoint, database migration, frontend runtime change, dependency change, Dockerfile/base-image change, cloud LLM, cloud vision, or a whole-product Kimi-level claim.

The harness uses deterministic fixture text and local K6 execution. It can write per-case PPTX, manifest, and safe-metadata artifacts into a caller-provided artifacts directory.

## Automated proxy scoring

RC1 includes conservative automated proxy scoring to confirm that the harness can collect comparable signals across all K0 cases. This is not a human visual/design benchmark and must not be used as an unqualified Kimi-level claim.

The report explicitly keeps:

```text
human_benchmark_review_required: true
kimi_level_claimed_by_rc1: false
whole_project_kimi_level_supported: false
```

## Operator command

```bash
python3 scripts/kw_rc1_golden_benchmark_harness.py \
  --repo-root . \
  --artifacts-dir logs/rc1-golden-benchmark-artifacts \
  --require-ready \
  --json
```

## Acceptance

RC1 is ready when all five K0 cases execute successfully, generate non-empty PPTX artifacts, produce manifests, preserve complete source-to-slide provenance, run Visual QA, pass K6 gates, and leave the no-Kimi-claim and no-feature-scope guards intact.

## Post-RC1 readiness guard

`kw_rc1_golden_benchmark_harness.py --require-ready` verifies that the K-phase closure commit is an ancestor of the current branch HEAD. It intentionally does not require the current HEAD to equal the closure commit, because RC1 functional/verdict commits are expected to come after K-phase closure on `8_K_Phase`.

This keeps the checkpoint strict about lineage while allowing release-candidate verification commits to be tested by the production readiness gate.

