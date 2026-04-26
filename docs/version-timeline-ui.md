# P3 Editable plan version timeline UI

P3 adds a read-only version timeline for generated presentations.

## Backend endpoint

```http
GET /presentations/{presentation_id}/versions
```

The endpoint returns safe version summaries ordered by `version_number` ascending.

It does not expose storage internals such as `storage_key`, `storage_uri`, or local file paths.

## Frontend behavior

The presentation detail panel now includes a **Version timeline** section.

The operator can:

- load the version timeline;
- select a historical version;
- load the selected version plan snapshot;
- load the selected version diff against its parent.

The first version has no parent, so selected diff is disabled for that version.

## Scope boundaries

P3 is read-only.

It intentionally does not add:

- rollback;
- mutation of historical versions;
- arbitrary pairwise diff;
- plan editing;
- PPTX preview.
