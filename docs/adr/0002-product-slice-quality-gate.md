# ADR 0002: Product Slice Quality Gate

## Status

Accepted

## Context

KR-7H correctly used many narrow layers to build a safe renderer-worker foundation. After that foundation closed, KR-7I through KR-7N continued to add useful deterministic contracts, but several layers remained too isolated from the end-to-end product workflow. The project goal is an offline/intranet, artifact-first, provenance-first KW Studio, not a repository of disconnected schemas and checks.

The project still forbids fake charts, fake images, unsupported Kimi-level claims, weakened guardrails, or production-quality claims without evidence. However, those prohibitions must not be used as an excuse for shallow patches.

## Decision

After a foundation closure gate, new KR patches must be small vertical product slices whenever feasible. A vertical product slice connects the new capability to at least one product path such as:

```text
planner or scenario decision;
backend API or service contract;
artifact bundle, manifest, provenance, or quality report;
Presentation Studio UI surface;
project-resident runner/checker validation.
```

A contract-only patch is allowed only when it is explicitly marked as `phase-entry scaffold` or `governance repair`, and the roadmap must name the follow-up integration patch required to raise it to product quality.

## Consequences

Future patches must document:

```text
what user-visible or artifact-visible behavior changed;
which previous KR layer was integrated or upgraded;
which product path exposes the result;
which limitations remain honest degraded/partial behavior;
which follow-up patch is mandatory if the current patch is only a scaffold.
```

KR-7O and later work must include remediation slices that connect KR-7I template/brand profiles, KR-7J source image selection, KR-7K data-backed charts, KR-7L layout plans, KR-7M UI, and KR-7N quality reports into the actual Slides workflow.

## Rejected alternatives

```text
Continue adding one isolated contract per roadmap phase and call each phase complete.
Make a broad unsafe production renderer rewrite in one patch.
Claim production/Kimi-level quality without render/provenance/quality evidence.
Hide missing integration behind fallback content or fake success metadata.
```
