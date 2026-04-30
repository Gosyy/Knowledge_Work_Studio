# Offline LLM Topology

## Recommended choice

KW Studio production/offline mode uses three servers.

```text
Server 1: KW Studio application node
Server 2: optional LLM gateway / heavy runtime node
Server 3: local GigaChat node
```

## Server 1 — KW Studio App Node

Runs:
- FastAPI backend
- Next.js frontend
- Postgres
- artifact storage
- task orchestration
- DOCX/PDF/Slides/Data workflows

Server 1 must not run heavyweight model inference by default.

## Server 2 — Optional Gateway / Heavy Runtime Node

May run:
- LiteLLM-compatible gateway
- Ollama/local fallback models
- embeddings
- OCR
- rerank
- heavy CPU modules
- future visual QA components

Server 2 is optional for the default GigaChat path.

## Server 3 — Local GigaChat Node

Runs:
- local GigaChat
- internal endpoint by ip:port

This is the default production LLM.

## Default path

```text
KW Studio Server 1
  → http://<server-3-ip>:<gigachat-port>
  → local GigaChat Server 3
```

## Optional gateway path

```text
KW Studio Server 1
  → http://<server-2-ip>:4000
  → LiteLLM-compatible gateway Server 2
  → http://<server-3-ip>:<gigachat-port>
  → local GigaChat Server 3
```

## Fallback/dev path

```text
KW Studio Server 1
  → Server 2 gateway
  → Ollama/local model on Server 2
```

## Provider priority

1. `gigachat` — default production provider
2. `litellm` — optional gateway transport
3. `ollama/local` — fallback/dev/experimental only, usually behind gateway
4. `fake` / `noop` — tests only

## Offline rules

Production/offline mode must not require:
- internet;
- public cloud LLM API;
- runtime package downloads;
- Docker Hub pulls;
- PyPI/npm access;
- external telemetry.

Allowed runtime communication:
- Server 1 → Server 3 GigaChat ip:port
- Server 1 → Server 2 gateway ip:port, only if gateway is enabled
- Server 2 → Server 3 GigaChat ip:port, only if gateway routes to GigaChat

Deny:
- public → any LLM port
- Server 1/2/3 → internet in production/offline runtime
- external model endpoints as defaults

## Environment examples

Direct local GigaChat:

```dotenv
DEPLOYMENT_MODE=offline_intranet
LLM_PROVIDER=gigachat
GIGACHAT_API_BASE_URL=http://10.0.0.30:8080
GIGACHAT_AUTH_URL=http://10.0.0.30:8080/oauth
GIGACHAT_MODEL=GigaChat-Pro
GIGACHAT_CLIENT_ID=CHANGE_ME_LOCAL_GIGACHAT_CLIENT_ID
GIGACHAT_CLIENT_SECRET=CHANGE_ME_LOCAL_GIGACHAT_CLIENT_SECRET
GIGACHAT_VERIFY_SSL=false
```

Optional LiteLLM-compatible gateway:

```dotenv
DEPLOYMENT_MODE=offline_intranet
LLM_PROVIDER=litellm
LITELLM_PROXY_BASE_URL=http://10.0.0.20:4000
LITELLM_MODEL=kw-default
LITELLM_API_KEY=CHANGE_ME_INTERNAL_LITELLM_KEY
```

## Hard rule

LiteLLM is not the default model. It is an optional gateway.

Ollama is not the default provider. It is fallback/dev/experimental.

GigaChat on Server 3 is the default production LLM.
