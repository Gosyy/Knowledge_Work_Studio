# RC2 Golden Benchmark Quality Review Report

RC2 is a release-candidate diagnostic checkpoint after RC1. It does not add a new product runtime feature. It turns the RC1 golden benchmark execution outputs into a machine-readable quality review map for renderer, provenance, visual QA, source faithfulness, and workflow follow-up work.

## Scope

RC2 runs the existing RC1 harness over the five K0 golden benchmark cases and then emits `rc2_quality_findings.json` under the selected artifacts directory. The report summarizes per-case findings, severities, evidence, and recommended next patch buckets.

RC2 is intentionally diagnostic:

- it preserves RC1 PPTX, manifest, and safe metadata artifacts;
- it generates renderer findings from conservative proxy scores, slide counts, and artifact payload size signals;
- it generates provenance findings from K5 coverage, fragment counts, source counts, and manifest evidence links;
- it generates visual QA findings from K4 status while explicitly noting that current QA is deterministic OOXML QA, not screenshot/raster review;
- it generates source-faithfulness findings, including whether deterministic fallback planning was used;
- it keeps human benchmark review mandatory.

## Non-goals

RC2 does not:

- add a public API endpoint;
- add a database schema migration;
- change frontend runtime behavior;
- change dependency versions;
- change Dockerfiles or base images;
- add cloud LLM or cloud vision;
- improve renderer/provenance/visual QA runtime behavior directly;
- claim that KW Studio is fully Kimi-level.

## Expected report semantics

A ready RC2 report means that the diagnostic harness executed and produced a follow-up map without blocking failures. Warnings are expected and useful. They are the point of RC2: a green RC1 pipeline does not mean the generated decks are good enough for a Kimi-level claim.

Recommended next tracks are:

- RCH1: renderer density/layout fixes;
- RCH2: provenance fragment quality/diversity fixes;
- RCH3: visual QA heuristic calibration;
- RC3: local GigaChat golden benchmark comparison.

## Release-readiness guard

`kw_rc2_golden_benchmark_quality_review.py --require-ready` verifies that the RC1 hotfix verdict commit is an ancestor of the current branch HEAD. It intentionally allows later RC commits after the RC1 hotfix while preserving strict lineage.

## Operator interpretation

RC2 gives a first honest diagnostic map of what should be improved next. It is not a substitute for human review of generated PPTX artifacts. The report is designed to prioritize controlled hardening patches rather than broad product rewrites.
