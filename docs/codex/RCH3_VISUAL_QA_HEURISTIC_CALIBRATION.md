# RCH3 — Visual QA heuristic calibration

## Status
Accepted only after targeted runner, full runner, and Docker smoke pass.

## Scope
RCH3 hardens the existing K4 visual QA runtime by calibrating deterministic local heuristics. It separates informational findings, operator-review warnings, and blocker defects so the golden benchmark can distinguish noisy layout signals from real delivery risks.

## Added capabilities
- calibrated info / warning / blocker severity split;
- minor-overlap informational findings to reduce false positive rework;
- blocker guard for extreme estimated text overflow;
- calibrated issue-count metadata;
- RCH3 checker and regression smoke tests;
- production readiness gate coverage.

## Non-goals
- no public API endpoint;
- no DB schema migration;
- no frontend runtime rewrite;
- no dependency or Docker/base-image change;
- no cloud vision or cloud LLM;
- no Kimi-level claim.

## Offline contract
RCH3 remains deterministic and local. It inspects local PPTX OOXML and safe metadata only.
