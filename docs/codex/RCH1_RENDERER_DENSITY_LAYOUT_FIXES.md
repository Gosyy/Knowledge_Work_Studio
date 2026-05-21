# RCH1 — Renderer density/layout fixes

RCH1 is a controlled renderer-hardening checkpoint after RC3. It improves the existing K3 deterministic renderer-quality layer for golden benchmark plans and live GigaChat-shaped plans without adding a new product runtime surface.

## Scope

- strengthen layout-family selection for comparison-like and data-like slides;
- rebalance dense bullets before approved-plan rendering;
- add deterministic comparison/data helper blocks when the plan shape implies them;
- preserve offline/local behavior and safe metadata;
- add a checker, smoke tests, and production-readiness coverage.

## Non-goals

- no public API endpoint;
- no DB schema migration;
- no frontend runtime change;
- no dependency version change;
- no Docker/base image change;
- no cloud LLM or cloud vision;
- no Kimi-level claim.

## Acceptance

RCH1 is accepted only when the targeted runner, post-push full runner, and Docker smoke pass on the selected profile.
