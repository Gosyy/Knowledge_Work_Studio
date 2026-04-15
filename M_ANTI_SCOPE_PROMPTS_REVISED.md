# M_SELF_CONTAINED_CODEX_PROMPTS_REVISED.md

Каждый prompt ниже самодостаточный: его можно копировать в Codex целиком без дополнительного global-блока.


---

# Prompt M0 — Create M-phase planning docs

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- START_HERE_INDEX.md
- DB_AND_STORAGE_ARCHITECTURE.md
- F_L_PHASE_ISSUE_PACK.md
- F_L_REVIEW_TACTICS.md
- docs/deployment/offline_intranet.md

Implement M0 only.

Issue scope:
Create M-phase planning documents:
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md

M-phase goal:
Move KW Studio from accepted backend MVP foundation to productization and production scaffold.

The issue pack must cover:
- M1 auth/users domain foundation
- M2 ownership enforcement
- M3 Alembic migration workflow
- M4 background job queue foundation
- M5 MinIO/S3 storage adapter
- M6 frontend API integration contract
- M7 observability baseline
- M8 binary source extraction

Allowed changes:
- documentation files only

Hard anti-scope:
- Do NOT implement backend code.
- Do NOT change runtime behavior.
- Do NOT change frontend.
- Do NOT change F–L architecture.
- Do NOT add dependencies.

Acceptance criteria:
- Each M issue has scope, anti-scope, allowed files, likely files, acceptance criteria, required tests, and stop conditions.
- Review tactics include Scope / Architecture / Truth-layer / Reality / Tests / Hygiene.
- Prompt pack is strict enough to run Codex issue-by-issue.

Run:
- python -m compileall backend
```

---

# Prompt M1 — Auth/users domain foundation

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- DB_AND_STORAGE_ARCHITECTURE.md
- backend/app/domain/
- backend/app/repositories/
- backend/app/integrations/database/bootstrap.py
- scripts/migrations/

Implement M1 only.

Issue scope:
Add auth/users domain foundation.

Allowed changes:
- user domain model
- password hash abstraction or safe password service interface
- user repository protocol
- Postgres user repository implementation
- SQLite user repository implementation only for tests/local dev consistency
- schema/bootstrap additions for users
- focused repository/domain tests
- minimal docs if needed

Adjacent issue firewall:
- M1 may create users and auth primitives.
- M1 must NOT enforce ownership over sessions/tasks/artifacts/files. That belongs to M2.
- M1 must NOT build login UI.
- M1 must NOT implement OAuth.
- M1 must NOT add frontend screens.
- M1 must NOT change existing task/session/artifact access behavior.
- M1 must NOT add broad RBAC.

Hard anti-scope:
- Do NOT redesign existing repositories.
- Do NOT change official execution flow.
- Do NOT change deployment profile.
- Do NOT introduce external auth providers.
- Do NOT store plaintext passwords.

Acceptance criteria:
- User is represented in domain and persistence code.
- User repository can create/get/list or equivalent minimal operations.
- Password handling is safe enough for foundation-level backend work.
- Existing tests pass.
- No ownership enforcement behavior changed.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M2 — Ownership enforcement

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/dependencies.py
- backend/app/api/routes/sessions.py
- backend/app/api/routes/tasks.py
- backend/app/api/routes/uploads.py
- backend/app/api/routes/artifacts.py
- backend/app/services/session_task_service.py
- backend/app/services/artifact_service.py
- backend/app/services/task_source_service.py
- backend/app/domain/
- backend/app/repositories/

Implement M2 only.

Issue scope:
Enforce explicit user ownership over:
- sessions
- tasks
- uploaded files
- stored files
- artifacts

Allowed changes:
- current-user dependency
- test-safe identity mechanism
- ownership fields where required
- repository methods needed for owner-aware lookup
- service-level ownership checks
- API tests proving cross-user access is denied

Adjacent issue firewall:
- M2 assumes M1 auth primitives exist.
- M2 must NOT redesign M1 auth primitives.
- M2 must NOT implement OAuth.
- M2 must NOT build frontend auth screens.
- M2 must NOT implement full RBAC.
- M2 must NOT change artifact generation behavior except to enforce ownership.

Hard anti-scope:
- Do NOT make ownership implicit through session IDs only.
- Do NOT allow user A to access user B resources.
- Do NOT bypass ownership in artifact download.
- Do NOT skip tests for cross-user denial.
- Do NOT change GigaChat/provider/storage behavior.

Acceptance criteria:
- User A cannot access user B sessions, tasks, uploads, stored files, or artifacts.
- Owner is explicit in persisted data or enforced through reliable relationships.
- Existing official flows still pass for the owning user.
- Cross-user access tests return 403 or 404 consistently.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M3 — Alembic migration workflow

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- DB_AND_STORAGE_ARCHITECTURE.md
- scripts/migrations/
- backend/app/integrations/database/bootstrap.py
- backend/app/core/config.py

Implement M3 only.

Issue scope:
Introduce proper Alembic workflow for Postgres schema evolution.

Allowed changes:
- alembic.ini
- migrations/env.py
- first Alembic migration matching current approved schema
- migration README/docs
- small smoke tests that migration files/config exist and are coherent
- dependency update only if required and safe

Adjacent issue firewall:
- M3 must NOT redesign schema.
- M3 must NOT add auth tables unless M1 is already accepted and schema alignment requires it.
- M3 must NOT implement background jobs.
- M3 must NOT remove existing bootstrap unless safely replaced and tests prove compatibility.

Hard anti-scope:
- Do NOT make SQLite production migration target.
- Do NOT drop current baseline behavior accidentally.
- Do NOT invent new product entities.
- Do NOT change API behavior.

Acceptance criteria:
- Alembic is documented as production migration path.
- Current approved schema is represented in a migration.
- Existing bootstrap compatibility is preserved or explicitly deprecated with safe tests.
- Existing tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M4 — Background job queue foundation

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/routes/tasks.py
- backend/app/services/task_execution_service.py
- backend/app/orchestrator/execution.py
- backend/app/repositories/execution_runs.py
- backend/app/domain/tasks/models.py

Implement M4 only.

Issue scope:
Add background job queue foundation for task execution.

Allowed changes:
- job domain model
- queue abstraction
- in-process test queue
- worker skeleton
- repository support if needed
- API execution mode or enqueue endpoint
- tests proving queued execution processes real task execution

Adjacent issue firewall:
- M4 must NOT implement Celery/RQ/Redis unless the issue pack explicitly allows it.
- M4 must NOT redesign task execution.
- M4 must NOT change artifact semantics.
- M4 must NOT add frontend.
- M4 must NOT add observability stack; that belongs to M7.

Hard anti-scope:
- Do NOT mark queued jobs succeeded without running real execution.
- Do NOT remove synchronous execution.
- Do NOT bypass provenance/source handling.
- Do NOT hide failed jobs as success.

Acceptance criteria:
- Synchronous execution still works.
- Queued execution has clear lifecycle.
- Worker skeleton processes through official coordinator/service path.
- Failed jobs are represented honestly.
- Tests prove queued execution creates expected task result/artifact.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M5 — MinIO/S3-compatible storage adapter

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/composition.py
- backend/app/deployment.py
- backend/app/integrations/file_storage/
- backend/app/repositories/storage.py
- docs/deployment/offline_intranet.md

Implement M5 only.

Issue scope:
Implement real S3-compatible storage adapter suitable for MinIO/offline intranet.

Allowed changes:
- S3CompatibleStorage or MinIOStorage adapter
- config wiring
- no silent local fallback
- tests using mocked client/fake interface
- readiness checks update
- docs update

Adjacent issue firewall:
- M5 must NOT change artifact business logic.
- M5 must NOT implement public cloud assumptions.
- M5 must NOT implement binary extraction.
- M5 must NOT implement auth.
- M5 must NOT change frontend.

Hard anti-scope:
- Do NOT hardcode credentials.
- Do NOT require public internet.
- Do NOT silently use local storage when MinIO/S3 is configured.
- Do NOT store binary payloads in Postgres.
- Do NOT fake remote storage success.

Acceptance criteria:
- STORAGE_BACKEND=minio or s3 uses real adapter path.
- Missing config fails readiness.
- Adapter calls are testable without public internet.
- Local storage still works.
- Existing artifact storage behavior is preserved.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M6 — Frontend API integration contract

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/api/routes/
- backend/app/api/schemas/
- backend/app/main.py
- .env.example

Implement M6 only.

Issue scope:
Create stable frontend-facing API contract for current backend MVP.

Allowed changes:
- API contract docs
- request/response examples
- OpenAPI/schema cleanup if non-breaking
- frontend config only if required for contract clarity
- schema stability tests

Adjacent issue firewall:
- M6 must NOT build full frontend UI.
- M6 must NOT redesign backend workflows.
- M6 must NOT implement auth UI.
- M6 must NOT change task execution behavior.
- M6 must NOT add new product capabilities.

Hard anti-scope:
- Do NOT break existing API tests.
- Do NOT rename endpoints without compatibility.
- Do NOT change response models unless necessary and tested.
- Do NOT introduce public-internet dependency.

Acceptance criteria:
- Frontend can understand how to call sessions, uploads, tasks, semantic tasks, artifacts, health, readiness.
- Request/response examples are documented.
- Current API behavior remains compatible.
- Tests pass.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M7 — Observability baseline

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/main.py
- backend/app/core/config.py
- backend/app/deployment.py
- backend/app/services/task_execution_service.py
- backend/app/orchestrator/execution.py

Implement M7 only.

Issue scope:
Add dependency-light production observability baseline.

Allowed changes:
- structured logging config
- request ID middleware
- request/response metadata logging
- task execution correlation logging
- readiness logging
- error logging
- optional dependency-free metrics skeleton

Adjacent issue firewall:
- M7 must NOT add full Prometheus/Grafana stack unless explicitly allowed.
- M7 must NOT add Sentry external calls.
- M7 must NOT implement background job queue.
- M7 must NOT change business behavior.
- M7 must NOT add frontend.

Hard anti-scope:
- Do NOT log secrets.
- Do NOT log file contents.
- Do NOT log GigaChat credentials or tokens.
- Do NOT make external network calls for observability.
- Do NOT alter API semantics.

Acceptance criteria:
- Logs include request/task correlation where available.
- Sensitive values are not logged.
- Existing tests pass.
- New tests cover request ID/logging behavior where practical.

Required checks:
- pytest -q
- python -m compileall backend
```

---

# Prompt M8 — Binary source extraction

## Global Codex contract for this issue

```text
Work from the repository root.

This is not a greenfield project.
F–L phase is accepted.
Do not re-litigate F–L architectural decisions.
Do not replace the composition root, official execution coordinator, storage model, provider model, or deployment profile unless this issue explicitly says so.

Current-branch-state rules:
- Work against the CURRENT checked-out branch state, not an assumed earlier snapshot.
- Inspect the live contents of each file you may change before planning.
- Do not generate a patch against stale file contents.
- If a previously changed file has drifted, re-plan against the live file instead of forcing an earlier patch shape.
- Prefer additive changes over broad rewrites.
- If patch compatibility is uncertain, stop and report exact conflicting files.

Mandatory before coding:
1. List files inspected.
2. Describe current behavior found.
3. List exact files planned for change.
4. Explain why each file is necessary for this issue.
5. State adjacent issues that are intentionally NOT being implemented.
6. State tests to add or update.

Mandatory after coding:
1. Summarize only this issue's changes.
2. List files changed.
3. Explicitly confirm adjacent issues were not implemented.
4. Explicitly confirm accepted F–L architecture was preserved.
5. List commands run.
6. Report test results.

Required checks:
- pytest -q
- python -m compileall backend

Stop conditions:
- If completing this issue requires adjacent issue work, implement only the smallest safe subset and report what remains blocked.
- If a target file has drifted in a way that makes the patch unsafe, stop and report the file.
- If a change would create fake success behavior, stop.
- If a change would silently fall back from a configured production service, stop.
```

## Global anti-scope rules for this issue

```text
Do NOT:
- Redesign accepted F–L architecture.
- Replace the composition root with route-local wiring.
- Reintroduce transitional orchestration surfaces.
- Make SQLite a production truth layer.
- Store binary files primarily in Postgres.
- Make non-GigaChat provider active in deployment.
- Add public-internet deployment assumptions.
- Add fake success paths.
- Hide missing infrastructure behind local fallback.
- Remove tests merely to make the suite pass.
- Touch frontend unless this issue explicitly allows it.
- Implement multiple M issues in one Codex run.
```

## Review gate for this issue

```text
Review dimensions:
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene

Reject if:
- adjacent issue work was implemented
- accepted F–L architecture was changed without explicit scope
- tests were removed without stricter replacement
- production config silently falls back to local/fake behavior
- fake implementation claims real capability
- frontend was changed outside scope
- public-internet dependency was introduced into offline intranet profile
- pytest or compileall fails
```

## Issue-specific instructions

```text
Read first:
- AGENTS.md
- M_PHASE_ISSUE_PACK.md
- M_REVIEW_TACTICS.md
- M_ANTI_SCOPE_PROMPTS_REVISED.md
- backend/app/services/task_source_service.py
- backend/app/services/docx_service/
- backend/app/services/pdf_service/
- backend/app/services/slides_service/
- backend/app/domain/metadata/models.py
- backend/app/repositories/

Implement M8 only.

Issue scope:
Add honest binary source extraction for supported formats.

Start with:
- DOCX text extraction
- PPTX outline/text extraction
- PDF text extraction only if a safe existing dependency or honest parser path exists

Allowed changes:
- extractor interfaces
- format-specific extractors
- TaskSourceService integration
- derived_contents caching/reuse
- tests with small generated sample binaries

Adjacent issue firewall:
- M8 must NOT redesign generation.
- M8 must NOT implement OCR.
- M8 must NOT add public-internet dependencies.
- M8 must NOT fake PDF extraction.
- M8 must NOT implement remote storage adapter.

Hard anti-scope:
- Do NOT claim unsupported binary formats work.
- Do NOT silently decode binary garbage as text.
- Do NOT bypass derived_contents cache.
- Do NOT weaken existing text-source behavior.
- Do NOT add broad heavyweight dependencies without justification.

Acceptance criteria:
- Supported binary uploaded/stored sources can feed official execution.
- Unsupported formats fail honestly with clear error.
- Extracted text is cached in derived_contents and reused.
- Existing prompt-only and text-source flows still pass.

Required checks:
- pytest -q
- python -m compileall backend
```
