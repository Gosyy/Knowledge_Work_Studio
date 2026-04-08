# KW Studio

KW Studio is an AI workspace for knowledge work.

It accepts user files and natural-language tasks, routes them through the appropriate workflow, and returns finished work products such as edited documents, summaries, presentation decks, and data analysis outputs.

## Start here

See:
- `README.start-here.md`
- `AGENTS.md`
- `docs/product-spec.md`
- `docs/roadmap.md`
- `docs/issue-pack.md`

## Quick start

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
- `http://localhost:8000/health`
