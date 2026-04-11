# START_HERE_INDEX.md

## F–L phase bundle
This bundle contains the core planning artifacts for the F–L implementation program.

## Key decisions
- Postgres is the single metadata truth layer
- Storage backend is the binary truth layer
- GigaChat is the only active LLM provider in deployment
- Deployment is offline intranet / remote Postgres / optional remote storage
- DOCX and PPTX outputs must be real valid formats
- No fake PDF behavior
- Real Python execution engine is required
