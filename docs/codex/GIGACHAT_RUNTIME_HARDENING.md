# KW Studio RF4 Local GigaChat Runtime Hardening

## Status

RF4 checkpoint: local GigaChat integration hardening.

RF4 hardens the direct local GigaChat production path after RF3 document ingestion and the RF2 slides runtime foundation. It does not start K-phase, does not add a cloud LLM, does not make LiteLLM mandatory, and does not change dependency or Docker policy.

## Scope

RF4 adds a narrow runtime validation and diagnostics layer for the default production LLM path:

- direct local GigaChat remains the default production LLM path;
- Server 3 hosts GigaChat and is reached by internal `ip:port` or private/internal DNS;
- Server 2 LiteLLM-compatible gateway remains optional explicit transport only;
- fake/noop providers remain development/test only and must not silently satisfy offline production runtime;
- operator diagnostics are safe, redacted, and avoid raw secret storage;
- mocked diagnostics prove success and timeout/failure operator messages without contacting public internet.

## Non-goals

RF4 intentionally does not:

- add a public API endpoint;
- add a DB schema migration;
- add a queue/event-store migration;
- change dependency versions;
- change Dockerfiles;
- run `npm audit fix` or `npm audit fix --force`;
- introduce a cloud LLM provider;
- route production through public internet;
- make LiteLLM mandatory;
- implement K-phase local GigaChat planning;
- claim Kimi-level or product-power capability.

## Acceptance

RF4 is accepted when:

- `python3 scripts/kw_gigachat_runtime_hardening_check.py --repo-root . --require-ready --json` passes;
- RF4 smoke tests pass;
- existing LLM provider/factory tests pass;
- production readiness includes the RF4 checker;
- full runner and Docker runtime smoke pass after commit/push;
- remote `7_Runtime_Foundation` matches the RF4 verdict commit.

## Next route

After RF4 acceptance, continue to RF closure, then K0. Do not start K-phase until RF closure is accepted.
