# Tool and Workflow Contracts

KW Studio should expose workflows through stable contracts. The LLM may plan and explain, but backend services must own execution, validation, and artifact integrity.

## Workflow contract

Each workflow should define:

- Input schema.
- Plan schema.
- Execution manifest.
- Artifact bundle layout.
- Quality report schema.
- Provenance manifest schema.
- Failure modes and retry rules.

Mandatory workflows:

- `docx`
- `pdf`
- `xlsx`
- `slides`
- `python_analysis`
- `browser_evidence`

## Tool contract principles

1. Tools accept structured inputs and return structured outputs.
2. Tools do not depend on local developer paths.
3. Tools report failures explicitly instead of silently producing partial artifacts.
4. Tools emit manifests and validation reports suitable for review.
5. Tools can be invoked by API, operator scripts, tests, and future CLI/SDK clients.

## LLM boundary

The LLM should be used for planning, summarization, transformation suggestions, narrative drafting, and explanations. It should not be trusted as the sole validator of generated files.

Validation belongs to deterministic backend checks whenever possible.
