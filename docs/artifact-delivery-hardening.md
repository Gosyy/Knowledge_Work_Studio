# P5 Artifact delivery hardening

P5 hardens generated artifact metadata and downloads.

## Public metadata

Artifact metadata endpoints now return a safe public schema:

```http
GET /artifacts/{artifact_id}
GET /sessions/{session_id}/artifacts
```

The response includes:

- id;
- session id;
- task id;
- display filename;
- content type;
- size;
- created time;
- download URL.

The response intentionally does not expose:

- `storage_key`;
- `storage_uri`;
- local filesystem paths;
- backend-internal storage layout.

## Download endpoint

```http
GET /artifacts/{artifact_id}/download
```

Download responses now include hardened headers:

- `Content-Disposition` with sanitized fallback filename;
- RFC 5987 `filename*` for UTF-8 filenames;
- `Content-Length`;
- `X-Content-Type-Options: nosniff`;
- `Cache-Control: private, no-store`.

The download filename is cleaned to prevent CRLF/header injection and path separator leakage.

## Scope boundaries

P5 does not change artifact generation, storage backends, or presentation revision behavior.
It only hardens public artifact metadata and download delivery.
