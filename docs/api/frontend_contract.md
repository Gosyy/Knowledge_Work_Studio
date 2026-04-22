# Frontend API contract for current backend MVP

This document is the stable frontend-facing API contract for the current MVP.
It documents the routes that the frontend may call today without relying on
private backend implementation details.

Base URL is supplied by `NEXT_PUBLIC_API_BASE_URL`.

## Health

### GET `/health`

Response example:

```json
{
  "status": "ok"
}
```

## Readiness

### GET `/ready`

Response example:

```json
{
  "status": "ready",
  "deployment_mode": "offline_intranet",
  "metadata_backend": "postgres",
  "storage_backend": "local",
  "llm_provider": "gigachat",
  "checks": {
    "offline_intranet_mode": true,
    "postgres_metadata_truth": true,
    "sqlite_not_runtime_truth": true,
    "postgres_dsn_configured": true,
    "storage_backend_supported": true,
    "storage_addressing_style_supported": true,
    "storage_configured": true,
    "llm_provider_gigachat_only": true,
    "gigachat_urls_configured": true,
    "gigachat_credentials_configured": true,
    "secret_key_configured": true
  },
  "errors": [],
  "warnings": []
}
```

## Sessions

### POST `/sessions`

Request example:

```json
{}
```

Response example:

```json
{
  "id": "ses_4f2b1c",
  "created_at": "2026-04-22T12:00:00Z"
}
```

### GET `/sessions/{session_id}`

Response example:

```json
{
  "id": "ses_4f2b1c",
  "created_at": "2026-04-22T12:00:00Z",
  "task_ids": ["task_71f0d3"],
  "upload_file_ids": ["upl_14be29"]
}
```

## Uploads

### POST `/uploads`

Multipart form fields:
- `session_id`
- `file`

Response example:

```json
{
  "id": "upl_14be29",
  "session_id": "ses_4f2b1c",
  "original_filename": "notes.txt",
  "stored_filename": "notes.txt",
  "content_type": "text/plain",
  "size_bytes": 2048,
  "storage_backend": "local",
  "storage_key": "uploads/ses_4f2b1c/upl_14be29/notes.txt",
  "storage_uri": "local://uploads/ses_4f2b1c/upl_14be29/notes.txt",
  "created_at": "2026-04-22T12:00:30Z"
}
```

## Tasks

### POST `/tasks`

Request example:

```json
{
  "session_id": "ses_4f2b1c",
  "task_type": "pdf_summary"
}
```

Response example:

```json
{
  "id": "task_71f0d3",
  "session_id": "ses_4f2b1c",
  "task_type": "pdf_summary",
  "status": "pending",
  "result_data": {},
  "error_message": null,
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-04-22T12:00:58Z"
}
```

### POST `/tasks/{task_id}/execute`

Request example:

```json
{
  "content": "Summarize the uploaded notes for the operator.",
  "uploaded_file_ids": ["upl_14be29"],
  "stored_file_ids": [],
  "document_ids": [],
  "presentation_ids": []
}
```

Response example:

```json
{
  "id": "task_71f0d3",
  "session_id": "ses_4f2b1c",
  "task_type": "pdf_summary",
  "status": "succeeded",
  "result_data": {
    "artifact_ids": ["art_903d8a"],
    "source_mode": "inline",
    "source_refs": []
  },
  "error_message": null,
  "started_at": "2026-04-22T12:01:00Z",
  "completed_at": "2026-04-22T12:01:03Z",
  "created_at": "2026-04-22T12:00:58Z"
}
```

### POST `/tasks/{task_id}/semantic`

Request example:

```json
{
  "content": "Rewrite this operator note for clarity.",
  "uploaded_file_ids": [],
  "stored_file_ids": [],
  "document_ids": [],
  "presentation_ids": [],
  "workflow": "rewriting",
  "instruction": "Make the text concise and professional."
}
```

### GET `/tasks/{task_id}`

Returns the current task state using the same task response schema.

## Artifacts

### GET `/sessions/{session_id}/artifacts`

Response example:

```json
[
  {
    "id": "art_903d8a",
    "session_id": "ses_4f2b1c",
    "task_id": "task_71f0d3",
    "filename": "summary.txt",
    "content_type": "text/plain",
    "storage_backend": "local",
    "storage_key": "artifacts/ses_4f2b1c/task_71f0d3/art_903d8a/summary.txt",
    "storage_uri": "local://artifacts/ses_4f2b1c/task_71f0d3/art_903d8a/summary.txt",
    "size_bytes": 512,
    "created_at": "2026-04-22T12:01:03Z"
  }
]
```

### GET `/artifacts/{artifact_id}`

Returns artifact metadata using the same artifact schema.

### GET `/artifacts/{artifact_id}/download`

Returns the binary payload with `Content-Disposition: attachment`.

## Queued execution

Queued execution is available but optional for the frontend MVP.

### POST `/tasks/{task_id}/enqueue`
Creates a queued task execution job.

### GET `/task-jobs/{job_id}`
Returns current queued job status.

### POST `/task-jobs/{job_id}/run`
Triggers the in-process worker path used in tests and local MVP operation.
