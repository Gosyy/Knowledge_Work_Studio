# S1 Offline LLM Topology

S1 fixes the production LLM topology for KW Studio without adding heavy runtime scope to the main application server.

## Required production layout

- **Server 1** runs KW Studio: backend, frontend, Postgres, artifact storage, workflow orchestration, diagnostics, and operator scripts.
- **Server 2** is optional and runs heavy CPU/runtime components: LiteLLM-compatible gateway, embeddings, rerank, OCR, and other heavyweight modules when introduced later.
- **Server 3** runs local GigaChat and exposes it only on an internal `ip:port` endpoint.

The default production path is:

```text
KW Studio Server 1 -> local GigaChat Server 3
```

The optional gateway path is:

```text
KW Studio Server 1 -> LiteLLM-compatible gateway Server 2 -> local GigaChat Server 3
```

The optional gateway does not replace GigaChat. It is only a transport/gateway abstraction for routing to the approved local GigaChat runtime.

## Offline rule

`DEPLOYMENT_MODE=offline_intranet` means runtime must not depend on internet-hosted LLM APIs. Operator setup can install dependencies from a controlled mirror, but production inference must use internal endpoints.

## Default and optional settings

```env
LLM_PROVIDER=gigachat
LLM_TRANSPORT_MODE=direct_gigachat
GIGACHAT_API_BASE_URL=http://<server3-ip>:<port>/api
GIGACHAT_AUTH_URL=http://<server3-ip>:<port>/auth
```

Optional Server 2 gateway:

```env
LLM_TRANSPORT_MODE=litellm_gateway
LITELLM_GATEWAY_URL=http://<server2-ip>:4000
LITELLM_GATEWAY_MODEL=gigachat-proxy
LITELLM_GATEWAY_API_KEY=<internal gateway token if enabled>
```

Ollama remains development/fallback only. It is not the production default and must not be selected as the offline provider.

## S1 acceptance

- `LLM_PROVIDER=gigachat` remains the only approved offline production provider.
- `LLM_TRANSPORT_MODE=direct_gigachat` is the default.
- `LLM_TRANSPORT_MODE=litellm_gateway` is allowed only as an internal gateway transport.
- Diagnostics and topology checks redact secrets.
- No heavy runtime, model download, or network inference is introduced by S1.
