# S9 Heavy Node Runtime

S9 documents the optional Server 2 heavy-node role without making it required for core KW Studio startup.

## Optional Server 2 modules

Server 2 may host:

- LiteLLM-compatible gateway
- embeddings
- OCR
- rerank
- heavy CPU workflow helpers

These are optional extensions. They must not block the base Server 1 application from starting.

## Offline/intranet boundary

Heavy-node endpoints must remain internal for `DEPLOYMENT_MODE=offline_intranet`.

No S9 check may require public internet access by default.

## Relationship to GigaChat

Server 3 local GigaChat remains the production LLM. Server 2 may expose a LiteLLM-compatible gateway in front of local GigaChat, but this is a transport decision, not a provider replacement.

## Contract check

Use:

```bash
python3 scripts/kw_litellm_gateway_check.py --repo-root . --allow-placeholders --require-ready
```

For an explicit gateway env file:

```bash
python3 scripts/kw_litellm_gateway_check.py \
  --repo-root . \
  --env-file .env.deploy \
  --mode litellm_gateway \
  --require-ready
```
