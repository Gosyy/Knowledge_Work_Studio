# S9 LiteLLM Gateway Topology

S9 defines the optional LiteLLM-compatible gateway topology for KW Studio.

## Canonical server roles

- Server 1: KW Studio application, backend, frontend, Postgres, artifact storage, and workflows.
- Server 2: optional LiteLLM-compatible gateway and heavy CPU runtime modules.
- Server 3: local GigaChat runtime reachable only by internal `ip:port`.

## Non-negotiable rule

LiteLLM is a gateway or transport abstraction only. It must not replace the default production provider.

Default production provider remains:

```text
LLM_PROVIDER=gigachat
```

Allowed transport modes:

```text
LLM_TRANSPORT_MODE=direct_gigachat
LLM_TRANSPORT_MODE=litellm_gateway
```

## Direct GigaChat mode

`direct_gigachat` remains the first-class offline production path.

Required configuration:

```text
GIGACHAT_API_BASE_URL=<internal Server 3 endpoint>
GIGACHAT_AUTH_URL=<internal Server 3 auth endpoint>
```

## Optional LiteLLM gateway mode

`litellm_gateway` routes through Server 2 and must target local/intranet resources.

Required configuration when selected:

```text
LITELLM_GATEWAY_URL=<internal Server 2 endpoint>
LITELLM_GATEWAY_MODEL=<gateway model alias for local GigaChat>
```

Optional sensitive value:

```text
LITELLM_GATEWAY_API_KEY=<redacted by diagnostics>
```

## Safety controls

S9 is contract-only. It does not introduce a network probe by default, does not require internet access, and does not add a cloud dependency.

Network probing must remain explicit and opt-in in a later step.
