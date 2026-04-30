# Artifact download UI and export history

R3 exposes the existing hardened artifact metadata and download API in the
frontend workspace.

## User workflow

1. Open the KW Studio workspace.
2. Go to **Artifact history**.
3. Enter a session id.
4. Click **Load artifacts**.
5. Review generated artifact metadata.
6. Use **Download artifact** to retrieve the generated export.

## Displayed metadata

The UI shows only safe public artifact metadata:

- filename
- content type
- size
- created time
- artifact id
- task id
- download link

## Forbidden metadata

The UI must never display or depend on:

- `storage_key`
- `storage_uri`
- `local://...`
- local filesystem paths
- backend artifact volume paths

## API contract

Frontend uses:

```text
GET /sessions/{session_id}/artifacts
```

Expected item shape:

```json
{
  "id": "art_123",
  "session_id": "ses_123",
  "task_id": "task_123",
  "filename": "deck.pptx",
  "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  "size_bytes": 1048576,
  "created_at": "2026-04-25T12:30:00Z",
  "download_url": "/artifacts/art_123/download"
}
```

Download links are resolved against `NEXT_PUBLIC_API_BASE_URL`.

## Error and empty states

The panel must show:

- an empty state when the session has no artifacts;
- a user-visible error when artifact metadata loading fails;
- a validation error if the public API response leaks internal storage fields.

## Non-goals

R3 does not add:

- artifact generation;
- storage backend changes;
- signed URL infrastructure;
- bulk export;
- artifact deletion;
- new auth or RBAC behavior.
