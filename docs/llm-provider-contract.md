# S1 LLM Provider Contract

The LLM provider contract separates product intent from transport mechanics.

## Product intent

KW Studio is an offline/intranet knowledge-work studio for DOCX, PDF, slides, data/Python, browser-assisted workflows, and verifiable artifacts. The production LLM is local GigaChat on Server 3.

## Provider identity

`LLM_PROVIDER` identifies the approved model provider family. In offline production it must remain:

```env
LLM_PROVIDER=gigachat
```

## Transport mode

`LLM_TRANSPORT_MODE` selects how KW Studio reaches the approved provider.

- `direct_gigachat`: Server 1 calls Server 3 GigaChat directly. This is the default production path.
- `litellm_gateway`: Server 1 calls a Server 2 LiteLLM-compatible gateway. The gateway routes to Server 3 GigaChat.

This design lets S-phase add Server 2 gateway/heavy modules without changing the default GigaChat provider decision.

## Non-goals for S1

S1 does not add model downloads, GPU scheduling, embeddings, OCR, browser automation runtime, prompt-chaining orchestration, or internet-hosted LLM APIs.

## Safety and observability

Use:

```bash
python scripts/kw_llm_topology_check.py --repo-root . --allow-placeholders --require-ready
```

The check prints topology status, server roles, endpoint classification, and redacted environment values. It does not call any endpoint and does not print tokens or credentials.
