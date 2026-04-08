# KW Studio — Start Here

This repository is prepared so Codex can start from a structured, non-empty codebase.

## Included
- backend FastAPI bootstrap
- backend health test
- docs and Codex guidance
- modular-monolith backend package boundaries for domain, orchestrator, services, repositories, integrations, and runtime
- empty product directories for frontend, infra, skills, and storage

## First local run

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
make install
make create-dirs
make test
make run
```

Health check:
- http://localhost:8000/health

## First Codex run

Use Prompt 1 from your prepared Codex prompt pack.
