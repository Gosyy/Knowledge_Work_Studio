# M_REVIEW_TACTICS.md

# KW Studio — M-phase Review Tactics

## Purpose

This document defines the review gate for M-phase work.

M-phase begins after accepted F–L backend MVP foundation.

The reviewer must protect:
- accepted architecture
- production truth layers
- offline intranet deployment model
- issue boundaries
- test reliability
- no fake success behavior

## Baseline to preserve

Accepted F–L baseline:
- Postgres is the metadata truth layer.
- Storage backend is the binary truth layer.
- GigaChat is the only active deployment provider.
- SQLite is dev/test only.
- Offline intranet deployment profile is approved.
- Composition root is explicit.
- Official execution coordinator is the only runtime orchestration path.
- Transitional orchestration surfaces are removed.
- DOCX/PPTX outputs must be real valid artifacts.
- PDF behavior must remain honest.
- Provenance/source lineage must not be broken.

## Review dimensions

Every M issue is reviewed across six dimensions:

```text
1. Scope
2. Architecture
3. Truth-layer
4. Reality
5. Tests
6. Hygiene
```

---

# 1. Scope review

## Ask

Did the change implement only the intended M issue?

## Pass if

- Only the requested issue was implemented.
- Adjacent issue work is explicitly not included.
- Files changed are explainable by the issue.
- Frontend was not touched unless explicitly allowed.
- Public internet assumptions were not introduced.

## Reject if

- M1 also implements M2 ownership.
- M2 also implements OAuth/frontend auth.
- M3 also redesigns schema.
- M4 adds a full external queue stack without approval.
- M5 also implements binary extraction.
- M6 builds a full UI.
- M7 adds external observability services.
- M8 fakes unsupported extraction.

---

# 2. Architecture review

## Ask

Does the change preserve accepted F–L architecture?

## Pass if

- Composition root remains the wiring authority.
- API routes do not become service factories.
- Official execution coordinator remains the runtime orchestration path.
- No transitional orchestration surfaces are reintroduced.
- Domain, repository, service, integration boundaries stay clear.

## Reject if

- Routes instantiate repositories/storage/providers directly.
- Old orchestration modules return.
- Business logic moves into FastAPI routes.
- Storage and metadata responsibilities are mixed.
- Provider-specific logic leaks into unrelated services.

---

# 3. Truth-layer review

## Ask

Are truth layers preserved?

## Pass if

- Postgres remains production metadata truth layer.
- SQLite remains dev/test only.
- Binary files remain in storage backend.
- Storage config never silently falls back to local when remote is configured.
- GigaChat remains only active deployment provider.

## Reject if

- SQLite is promoted to production path.
- Binary blobs are primarily stored in Postgres.
- MinIO/S3 misconfiguration silently uses local storage.
- Fake/noop provider becomes deployment-capable.
- Readiness checks are weakened.

---

# 4. Reality review

## Ask

Does the implementation do real work or fake success?

## Pass if

- Claimed features are real.
- Missing infrastructure fails loudly.
- Unsupported formats fail honestly.
- Tests verify behavior rather than only object existence.
- Error messages are explicit.

## Reject if

- Jobs are marked succeeded without execution.
- Remote storage adapter pretends to save without persistence.
- Binary extraction returns placeholder text.
- PDF extraction claims support without real extraction.
- Auth accepts any token as production behavior.
- Observability claims metrics without actual data source.

---

# 5. Tests review

## Required checks

Every implementation issue must run:

```bash
pytest -q
python -m compileall backend
```

Documentation-only issues must at least run:

```bash
python -m compileall backend
```

## Pass if

- Existing tests pass.
- New behavior has focused tests.
- Tests cover failure cases where important.
- Tests do not require public internet.
- Tests do not depend on real external credentials.

## Reject if

- Tests were deleted to pass.
- Tests assert only superficial imports for real behavior.
- Tests require public services.
- Cross-user access is not tested in M2.
- Remote storage behavior is not tested in M5.
- Unsupported binary format behavior is not tested in M8.

---

# 6. Hygiene review

## Ask

Is the diff clean and maintainable?

## Pass if

- No temporary patch-runner files are committed.
- No `__pycache__`, `.pyc`, local artifacts, logs, or secrets are committed.
- Names are clear and consistent.
- Errors are explicit.
- Docs match implementation.
- Config examples do not contain real secrets.

## Reject if

- `apply_*.py` files are committed.
- Secrets or tokens appear in repo.
- Generated artifacts are accidentally committed.
- Duplicate imports or dead code remain.
- Docs claim features not implemented.
- Formatting/typing is careless.

---

# Issue-specific review gates

## M0 review
Pass if planning docs only, no runtime code changes, M1–M8 are clearly scoped, and review tactics are strict enough.
Reject if implementation code is included or issue boundaries are vague.

## M1 review
Pass if user domain and persistence foundation exists, passwords are not plaintext, and ownership is not enforced yet.
Reject if login UI/OAuth/RBAC appears or existing access behavior changes.

## M2 review
Pass if ownership is explicit and tested, cross-user access is denied, and artifact download is protected.
Reject if session ID alone is treated as ownership or cross-user tests are missing.

## M3 review
Pass if Alembic workflow exists and maps current schema, bootstrap compatibility is preserved or safely deprecated, and production migration path is documented.
Reject if schema is redesigned or SQLite becomes production migration target.

## M4 review
Pass if queued execution runs through real official path, synchronous execution still works, and job failure is honest.
Reject if queue marks success without execution or source/provenance handling is bypassed.

## M5 review
Pass if MinIO/S3 adapter is real enough to save/read/delete/exists, misconfigurations fail loudly, and local storage still works.
Reject if remote storage silently falls back to local, credentials are hardcoded, or public internet is required.

## M6 review
Pass if API contract is documented, request/response examples are accurate, and backend behavior remains compatible.
Reject if full UI work appears or endpoints are renamed without compatibility.

## M7 review
Pass if request/task correlation exists, secrets are not logged, and no external observability calls are required.
Reject if Sentry/Prometheus/Grafana stack is added without scope or logs include content/secrets.

## M8 review
Pass if supported binary formats extract real text/outline, unsupported formats fail honestly, and derived content cache is reused.
Reject if OCR is added, PDF extraction is fake, or binary garbage is silently decoded as valid content.

---

# Verdict format

Use one of:

```text
M# verdict: ACCEPT
M# verdict: ACCEPT-CANDIDATE
M# verdict: HOLD
M# verdict: REJECT
```

## ACCEPT
Use when scope is correct, tests pass, architecture is preserved, no hygiene issues exist, and acceptance criteria are met.

## ACCEPT-CANDIDATE
Use when tests pass and implementation appears correct, but untracked files, CI, or final diff still need verification.

## HOLD
Use when a likely fixable issue exists, more output/diff is needed, tests have not been shown, or untracked files need review.

## REJECT
Use when scope was violated, tests fail, architecture was broken, fake behavior was introduced, or production truth-layer rules were violated.

---

# Required final review checklist

Before accepting any M issue, verify:

```text
[ ] git status --short reviewed
[ ] git diff --stat reviewed
[ ] changed files match issue scope
[ ] no patch-runner files committed
[ ] no secrets committed
[ ] pytest -q passed
[ ] python -m compileall backend passed
[ ] adjacent issues not implemented
[ ] F–L architecture preserved
[ ] docs updated if behavior/config changed
```
