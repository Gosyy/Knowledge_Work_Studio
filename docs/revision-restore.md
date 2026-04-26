# P4 Revision restore and rollback

P4 adds a deliberate rollback/restore operation for generated presentations.

## Backend endpoint

```http
POST /presentations/{presentation_id}/versions/{version_id}/restore
```

Request:

```json
{
  "confirmation": "RESTORE",
  "change_summary": "Restore previous accepted version",
  "task_id": "optional_task_id"
}
```

The confirmation field must be exactly `RESTORE`.

## Restore semantics

Restore is non-destructive:

- historical `presentation_versions` rows are not deleted;
- historical rows are not mutated;
- stored files are not overwritten;
- restore creates a new `PresentationVersion`;
- the new restore version points to the target version's stored file;
- the presentation's `current_file_id` is moved to the target file;
- the restore version's parent is the previous latest version;
- the target plan snapshot is copied onto the restore version so future revisions use the restored editable plan.

## Frontend behavior

The version timeline includes a restore control:

1. load version timeline;
2. select a historical version;
3. type `RESTORE`;
4. click **Restore selected version**.

After restore, the timeline refreshes and the presentation metadata refreshes.

## Scope boundaries

P4 does not implement:

- destructive rollback;
- mutation of historical rows;
- arbitrary branching UI;
- collaborative conflict handling;
- plan editing.
