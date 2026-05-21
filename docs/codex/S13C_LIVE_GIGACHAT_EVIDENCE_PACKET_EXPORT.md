# S13c — live GigaChat evidence packet export for human review

S13c packages the already-completed S13b `public_api_dev` GigaChat live outputs into a human-review evidence packet for the 12 selected benchmark scenarios.

## Scope

S13c is an export/packaging stage. It does not run live GigaChat generation again. It requires prior S13b live output evidence and prepares review-ready artifacts:

- packet index JSON;
- per-scenario evidence packet JSON;
- per-scenario model response summary JSON;
- pending human review worksheet JSON;
- reviewer instructions markdown;
- operator handoff README;
- archive manifest JSON.

## Required live inputs

- `s13b_live_generation_manifest.json`;
- scenario model response JSON files;
- response digests;
- public_api_dev route summary;
- credential safety summary.

## Safety boundaries

S13c must preserve the following boundaries:

- credentials are not recorded;
- raw secret values are not recorded;
- public_api_dev is recorded as public API evidence only;
- public_api_dev is not Server 3 local_intranet proof;
- human review remains pending;
- human review results are not fabricated;
- scenarios are not auto-approved;
- selected offline workflow parity is not claimed;
- generic Kimi-level achieved is not claimed.

## Review state

The exported worksheets must remain in `pending_human_review` until a human reviewer completes them.

Allowed future claim wording remains:

```text
Kimi Slides-class offline workflow parity for selected benchmark scenarios.
```

That wording is still not supported by S13c alone. It requires completed human review results and a later ingest/final dossier stage.
