# RC3 — Local GigaChat Golden Benchmark Comparison

RC3 is a release-candidate benchmark checkpoint after RC2. It compares the accepted deterministic fallback baseline against a GigaChat planning path.

RC3 is intentionally a benchmark/comparison harness, not a product runtime feature patch.

## Supported provider routes

### Production target route

The preferred production/offline target remains the local intranet GigaChat endpoint on Server 3:

```bash
export KW_RC3_GIGACHAT_ROUTE="local_intranet"
export KW_RC3_GIGACHAT_ENDPOINT="http://<server3-ip>:<port>/<completion-path>"
export KW_RC3_GIGACHAT_MODEL="local-gigachat"
```

### Temporary public API development route

For development on profile 1 before Server 3 is available, RC3 can use the public GigaChat API as an explicit dev-only comparison route:

```bash
export KW_RC3_GIGACHAT_ROUTE="public_api_dev"
export KW_RC3_GIGACHAT_ENDPOINT="https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
export KW_RC3_GIGACHAT_AUTH_URL="https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
export KW_RC3_GIGACHAT_MODEL="GigaChat"
export KW_RC3_GIGACHAT_SCOPE="GIGACHAT_API_PERS"
```

Provide one of the following credential inputs through shell environment only:

```bash
# Preferred: Authorization Key copied from the GigaChat project UI.
export KW_RC3_GIGACHAT_AUTHORIZATION_KEY="<authorization-key>"

# Alternative: let RC3 build the Basic key from Client ID and Client key.
export KW_RC3_GIGACHAT_CLIENT_ID="<client-id>"
export KW_RC3_GIGACHAT_CLIENT_SECRET="<client-key>"

# Alternative: pre-issued bearer value for short-lived manual runs.
export KW_RC3_GIGACHAT_ACCESS_TOKEN="<access-token>"
```

If the host does not trust the public GigaChat certificate chain yet, a dev-only run may disable certificate verification:

```bash
export KW_RC3_GIGACHAT_SSL_VERIFY=0
```

Do not commit these values. Do not place them into `.env.deploy`, `.npmrc`, `.proxy.env`, or repository files.

To require that the GigaChat path is actually used for every golden case:

```bash
export KW_RC3_REQUIRE_LOCAL_GIGACHAT=1
```

The name is kept for compatibility with the K1/K6 local-GigaChat terminology; in public dev mode the RC3 report marks `gigachat_provider_route=public_api_dev`, `production_route_verified=false`, and `offline_intranet_route_verified=false`.

## What RC3 verifies

- The five K0 golden benchmark fixtures still execute through the accepted K6 workflow.
- The deterministic fallback baseline remains available and deliverable.
- If a GigaChat route is configured, the same cases are attempted through that provider.
- RC3 records whether K1 actually used GigaChat output or fell back because the endpoint was unavailable or the response was not parseable as compact JSON.
- RC3 compares plan digests, artifact sizes, visual QA scores, and provenance coverage status between fallback and GigaChat paths.

## Non-goals

RC3 does not add a public API endpoint, DB migration, frontend runtime, dependency version change, Docker/base image change, product cloud LLM, product cloud vision, or Kimi-level claim.

The public API route is a dev/test override only. It does not verify the target offline/intranet topology.

## Expected next tracks

- RCH1 — renderer density/layout fixes.
- RCH2 — provenance fragment quality/diversity fixes.
- RCH3 — visual QA heuristic calibration.


## RC3b parser hardening

RC3b hardens only the benchmark harness provider for public GigaChat development runs. Real public GigaChat responses may contain fenced JSON, nested plan objects, localized keys, JSON arrays, or markdown slide outlines even when the prompt asks for compact JSON.

The RC3b normalization layer converts those response shapes into the compact K1 plan schema before K1 parses the provider response. This prevents false fallback in RC3 comparison while keeping the product K1/K6 runtime unchanged.

RC3b remains a development comparison checkpoint. A public API route does not verify the production offline/intranet Server 3 route.

## RC3c response-normalization hotfix

Public GigaChat dev-mode responses may arrive as fenced JSON, nested JSON,
localized keys, markdown outlines, or plain natural-language outlines. RC3c
keeps this handling scoped to the RC3 harness provider: it normalizes those
responses into the compact K1 schema before K1 parsing and falls back to a
conservative completion-text-derived plan only inside the public-api dev
comparison route. This prevents response-shape variance from silently turning
RC3 into deterministic fallback while preserving the production/offline
contract.

RC3c does not add a product runtime feature, endpoint, DB migration, frontend
runtime, dependency change, Docker change, cloud production route, or Kimi-level
claim.

## RC3 response-normalization hotfix

RC3 hotfix note: public API dev responses are canonicalized into the compact K1 JSON plan schema before comparison; this remains harness-only and does not change production K1/K6 runtime behavior.

