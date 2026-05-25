# ADR 0001: Assistant Decision Governance

## Status

Accepted

## Context

KW Studio has accumulated many critical engineering rules across chat history, migration handoff notes, KR roadmaps, agent instructions, runtime guardrails, and test rationalization plans. The rules are valid, but they are spread across multiple documents. This makes it too easy for an assistant to forget a rule, simplify a task, produce a patch without a local full-history checkout, or hide a product failure behind a fallback.

## Decision

KW Studio will keep a project-resident assistant decision governance layer:

```text
docs/ASSISTANT_OPERATING_RULES.md
docs/DEFINITION_OF_DONE.md
docs/PROJECT_PROHIBITIONS.md
docs/QUALITY_MATRIX.md
docs/templates/PRE_PATCH_REPORT_TEMPLATE.md
docs/templates/POST_PATCH_REPORT_TEMPLATE.md
docs/templates/LOG_ANALYSIS_TEMPLATE.md
scripts/kw_assistant_governance_check.py
```

`AGENTS.md`, `CODEX_PROJECT_BRIEFING.md`, and `PROJECT_MIGRATION_HANDOFF.md` must reference this layer. The project full runner must execute the governance checker so missing governance documents or broken links fail validation.

## Consequences

Future assistants must:

```text
verify local full-history checkout before code work;
use `.venv` for validation;
complete pre-patch and post-patch reasoning;
maintain documentation as structured source-of-truth files;
add or update ADRs for cross-cutting decisions;
update QUALITY_MATRIX.md when workflow maturity changes;
update PROJECT_PROHIBITIONS.md when new forbidden shortcuts are discovered;
use log evidence for ACCEPT / REJECT / PARTIAL decisions.
```

This adds a small maintenance cost, but it prevents undocumented shortcuts and reduces dependence on chat memory.

## Rejected alternatives

```text
Rely only on chat memory.
Rely only on AGENTS.md without a machine-checkable governance layer.
Put every rule into PROJECT_MIGRATION_HANDOFF.md and keep extending it indefinitely.
Accept patches based only on targeted tests or assistant claims.
```
