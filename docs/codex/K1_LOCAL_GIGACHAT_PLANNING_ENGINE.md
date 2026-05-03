# K1 — Local GigaChat Planning Engine

## Status

K1 starts after accepted K0 on branch `8_K_Phase`.

K1 adds the first product-power runtime component in K-phase: a source-aware, outline-first planning engine that uses direct local GigaChat when available and falls back to a deterministic local planner when the local model is unavailable.

K1 does not claim that KW Studio is Kimi-level. It is one planning-engine step toward the K0 rubric.

## Runtime contract

K1 input: source text, audience, deck goal, target slide count, and optional source references.

K1 output: `PresentationPlan`, slide titles, bullets, story-arc stages, layout hints, source notes, safe metadata, and deterministic fallback status.

## Local GigaChat path

```text
source text + source refs
-> safe prompt construction
-> local GigaChat provider
-> parse compact JSON plan
-> PresentationPlan
```

The provider must be `gigachat` in production mode. LiteLLM-compatible providers are not silently accepted as K1 production planners.

## Deterministic fallback

When local GigaChat is not configured, times out, or returns invalid response, K1 can produce a deterministic local plan if fallback is enabled. This is explicit in safe metadata and is not presented as Kimi-level planning.

## Safety

K1 stores prompt/source digests, provider/model labels, source reference count, and safe flags. It does not store raw source text, raw prompt, or secrets.

## Non-goals

No public API endpoint, DB migration, Dockerfile change, dependency change, cloud LLM fallback, mandatory LiteLLM, visual QA runtime, renderer upgrade, or Kimi-level claim.
