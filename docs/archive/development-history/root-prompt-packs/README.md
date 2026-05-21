# Root prompt-pack archive

This directory contains historical root-level prompt packs and old runbooks that
were moved during KR-3F controlled archive/delete readiness batch 1.

These files are kept for forensic recovery and project-history audit only. They
are no longer active product documentation and must not be used as the source of
truth for KW Studio product behavior.

Canonical product and operator documentation lives under:

```text
docs/product/
docs/architecture/
docs/workflows/
docs/quality/
docs/operators/
docs/refactor/
```

## KR-3F batch 1 moves

```text
F_L_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/F_L_ANTI_SCOPE_PROMPTS_REVISED.md
M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/M9_M15_ANTI_SCOPE_PROMPTS_REVISED.md
N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/N_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/O_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
PROMPTS_1_5.md -> docs/archive/development-history/root-prompt-packs/PROMPTS_1_5.md
R_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md -> docs/archive/development-history/root-prompt-packs/R_PHASE_ANTI_SCOPE_PROMPTS_REVISED.md
R_PHASE_ISSUE_PACK.md -> docs/archive/development-history/root-prompt-packs/R_PHASE_ISSUE_PACK.md
```

## Guardrail

Do not move `docs/codex` as part of this batch. `docs/codex` remains deprecated
development history, but physical archive/delete remains blocked until direct
checker and test dependencies are retired.
