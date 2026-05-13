# P10-5a GigaChat API golden benchmark execution

- status: `controlled_live_benchmark_checkpoint`
- branch: `9_Product_Release_Hardening`
- baseline before patch: `0e29e74b3f275d9c3fbfbd517ff212bf62c88c56`
- GigaChat route used by this checkpoint: `public_api_dev`
- Kimi-level claimed: `False`

## Purpose

P10-5a runs the golden benchmark through the real GigaChat API development route before the P10-5 release decision dossier.

This checkpoint is deliberately named `P10-5a` rather than `strict local GigaChat` because the operator requested the internet/key-based route used in earlier RC3 experiments. That route is a useful real-provider benchmark, but it is not proof that the production offline Server 3 intranet topology is working.

## What P10-5a verifies

P10-5a wraps the accepted RC3 comparison harness in a strict mode:

- the route is forced to `public_api_dev`;
- shell environment credentials are required for live execution;
- silent deterministic fallback is forbidden;
- all five golden benchmark cases must attempt and use GigaChat output;
- fallback and GigaChat artifacts are generated for comparison;
- the generated report preserves the future human re-review boundary.

## Required live environment

Credentials must be provided through shell environment only. Do not commit them and do not paste them into logs.

Preferred public API development route:

```bash
export KW_RC3_GIGACHAT_ROUTE="public_api_dev"
export KW_RC3_GIGACHAT_ENDPOINT="https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
export KW_RC3_GIGACHAT_AUTH_URL="https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
export KW_RC3_GIGACHAT_MODEL="GigaChat"
export KW_RC3_GIGACHAT_SCOPE="GIGACHAT_API_PERS"
export KW_RC3_REQUIRE_LOCAL_GIGACHAT=1
export KW_RC3_GIGACHAT_TIMEOUT_SECONDS=120
```

Then provide exactly one supported credential form in the shell:

```bash
export KW_RC3_GIGACHAT_AUTHORIZATION_KEY="<authorization-key>"
# or
export KW_RC3_GIGACHAT_CLIENT_ID="<client-id>"
export KW_RC3_GIGACHAT_CLIENT_SECRET="<client-key>"
# or
export KW_RC3_GIGACHAT_ACCESS_TOKEN="<access-token>"
```

If the local OS certificate chain does not trust the public GigaChat endpoint yet, a development-only run may use:

```bash
export KW_RC3_GIGACHAT_SSL_VERIFY=0
```

## Non-goals

P10-5a does not add a production cloud LLM route to KW Studio. It does not verify the Server 3 offline/intranet GigaChat topology. It does not change approval state, does not auto-approve golden decks, and does not claim Kimi-level parity.

P10-5a does not add product APIs, database migrations, frontend runtime changes, dependency changes, Docker/base-image changes, or public-internet runtime requirements for default production.

## Acceptance

P10-5a is accepted when:

- the static checker reports `ready` without credentials;
- the live runner reports `ready` with `--live --require-gigachat-used`;
- all five golden cases use GigaChat output;
- `comparison_status` is `compared_local_gigachat_to_fallback`;
- production readiness includes only the static P10-5a contract step;
- full runner passes with only known non-blocking warnings;
- Docker smoke passes on profile 2.
