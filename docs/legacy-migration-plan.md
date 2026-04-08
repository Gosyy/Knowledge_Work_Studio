# Legacy Migration Inventory and Plan (kernel_clean → KW Studio)

## Scope and objective

This document inventories selected legacy areas from the referenced `kernel_clean` codebase and proposes a phased migration plan into the current KW Studio modular-monolith architecture.

In-scope legacy areas:
- jupyter kernel runtime
- kernel server
- browser runtime
- docx skill assets
- pdf skill assets
- slides prompt/tool assets (if relevant)

Target locations in KW Studio:
- `backend/app/runtime/kernel/`
- `backend/app/runtime/browser/`
- `skills/docx/`
- `skills/pdf/`
- `backend/app/services/docx_service/`
- `backend/app/services/pdf_service/`
- `backend/app/services/slides_service/prompts/`

---

## Inspection notes (current workspace)

### What was inspected in this repository
- Runtime targets currently contain only bootstrap placeholders:
  - `backend/app/runtime/kernel/.gitkeep`
  - `backend/app/runtime/browser/.gitkeep`
- Skill and service prompt targets are currently placeholders:
  - `skills/docx/.gitkeep`
  - `skills/pdf/.gitkeep`
  - `backend/app/services/docx_service/prompts/.gitkeep`
  - `backend/app/services/pdf_service/prompts/.gitkeep`
  - `backend/app/services/slides_service/prompts/.gitkeep`

### Availability of legacy source (`kernel_clean`)
- No local git branch, remote ref, or mounted directory named `kernel_clean` was available in this environment at planning time.
- Because the reference source is not mounted, the inventory below is a **migration intake map** with explicit verification gates before code movement.

---

## Migration inventory matrix

> Status labels:
> - **Reusable**: likely can be migrated with minimal changes after verification.
> - **Reference-only**: useful as design reference, not copied directly.
> - **Needs refactor**: expected to require structural changes before migration.

| Legacy area | Expected legacy artifacts to inspect in `kernel_clean` | KW Studio target | Initial disposition | Why |
|---|---|---|---|---|
| Jupyter kernel runtime | kernel lifecycle manager, execution client, session wrappers, heartbeat/interrupt handlers | `backend/app/runtime/kernel/` | Needs refactor | Must isolate runtime-side concerns from business/services and align with restart-safe adapters. |
| Kernel server | HTTP/WebSocket server bootstrap, auth/token validation, kernel routing endpoints | `backend/app/runtime/kernel/` (adapter layer) | Reference-only + partial reusable | Endpoint semantics likely reusable, but server entrypoint must be adapted to modular-monolith integration boundaries. |
| Browser runtime (internal) | browser session manager, tool wrappers, page/screenshot automation utilities | `backend/app/runtime/browser/` | Needs refactor | Must remain internal-only and separated from user-facing API/business orchestration layers. |
| DOCX skill assets | prompt templates, editing instructions, transformation snippets | `skills/docx/` and `backend/app/services/docx_service/prompts/` | Reusable | Prompt/assets are generally portable; add versioning + schema metadata. |
| PDF skill assets | summary/report prompts, extraction templates, rubric assets | `skills/pdf/` and `backend/app/services/pdf_service/prompts/` | Reusable | Prompt/assets are portable with metadata normalization. |
| Slides prompt/tool assets | deck-structure prompts, speaker-note templates, slide tool config | `backend/app/services/slides_service/prompts/` | Reusable + needs refactor | Prompt text reusable; tool binding/config likely needs adaptation to new orchestrator tool routing contracts. |

---

## File/module mapping template (to execute once `kernel_clean` is mounted)

Use this mapping worksheet during actual migration PRs.

| Legacy source module/file | New target module/file | Migration type | Notes |
|---|---|---|---|
| `kernel_clean/<kernel-runtime-module>.py` | `backend/app/runtime/kernel/<adapter>.py` | Refactor | Move runtime mechanics only; keep service logic out of runtime package. |
| `kernel_clean/<kernel-server-entry>.py` | `backend/app/runtime/kernel/server_adapter.py` | Refactor | Wrap as internal adapter; avoid exposing directly as standalone app surface. |
| `kernel_clean/<browser-runtime-module>.py` | `backend/app/runtime/browser/<module>.py` | Refactor | Enforce internal-only boundary and explicit dependency injection. |
| `kernel_clean/<docx-prompts-or-assets>` | `skills/docx/` and/or `backend/app/services/docx_service/prompts/` | Reuse | Keep immutable prompt assets separate from execution code. |
| `kernel_clean/<pdf-prompts-or-assets>` | `skills/pdf/` and/or `backend/app/services/pdf_service/prompts/` | Reuse | Normalize naming, metadata, and versioning. |
| `kernel_clean/<slides-prompts>` | `backend/app/services/slides_service/prompts/` | Reuse/Refactor | Decouple prompt assets from any legacy execution wrappers. |

---

## Risk register (explicit)

1. **Tight coupling between kernel server and workflow logic** (High)
   - Risk: business-side decisions leak into runtime.
   - Mitigation: enforce adapter interfaces in `runtime/*`; keep orchestration in `orchestrator/` and services in `services/`.

2. **Browser runtime accidentally exposed as user-facing feature** (High)
   - Risk: conflicts with MVP boundary (browser runtime internal-only).
   - Mitigation: no public API routes directly invoking browser runtime; only internal orchestrator/service calls.

3. **Prompt assets copied without provenance/versioning** (Medium)
   - Risk: hard-to-audit behavior drift.
   - Mitigation: add prompt manifest metadata (source, version, checksum, owner) in each skills/prompts folder.

4. **Legacy global state/singletons in runtime code** (High)
   - Risk: restart and test instability.
   - Mitigation: dependency-injected factories; no import-time side effects.

5. **Transport/protocol mismatch for kernel comms** (Medium)
   - Risk: brittle integration when replacing stubs.
   - Mitigation: add contract tests around runtime adapter interfaces before wiring end-to-end.

---

## Phased migration plan

### Phase A — Intake and verification (documentation-first)
- Mount/fetch `kernel_clean` into a read-only location.
- Enumerate concrete files for each legacy area.
- Tag each file as `reusable`, `reference-only`, or `needs-refactor` with rationale.
- Produce a checksum/version inventory for prompt assets.

### Phase B — Runtime adapter extraction
- Extract kernel runtime primitives into `backend/app/runtime/kernel/` adapters.
- Extract browser runtime primitives into `backend/app/runtime/browser/` adapters.
- Add interface-level tests (no workflow coupling).

### Phase C — Service boundary integration
- Integrate runtime adapters behind `docx_service`, `pdf_service`, and `slides_service` boundaries.
- Keep FastAPI endpoints thin and unchanged in responsibility.
- Add orchestrator-to-service contract tests.

### Phase D — Prompt/skill asset migration
- Migrate DOCX/PDF/slides prompt assets with manifest metadata.
- Normalize file names and directory conventions.
- Add smoke tests validating prompt discovery/loading.

### Phase E — Stabilization and hardening
- Add error taxonomy, structured logging, and retry boundaries.
- Add safe fallbacks for unsupported legacy behaviors.
- Complete migration runbook and rollback strategy.

---

## Definition of done for migration PRs

Each migration PR should include:
- explicit source→target mapping table for touched files,
- risk classification for migrated files,
- tests for new adapter/service contracts,
- no import-time side effects,
- confirmation that `GET /health` and existing bootstrap behavior remain intact.

