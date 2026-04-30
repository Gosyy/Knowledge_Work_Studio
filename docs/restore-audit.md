# Restore audit metadata and safer confirmation UX

R4 hardens non-destructive presentation version restore.

## Existing restore semantics preserved

Restore still works by creating a new presentation version:

- historical versions are not deleted;
- historical versions are not mutated;
- the selected target version file becomes the current presentation file;
- the target version plan snapshot is copied to the new restore version;
- owner-scoped access checks run before restore execution.

## Added audit metadata

Restore requests may now include:

- `confirmation_target_version_id`
- `restore_reason`
- `change_summary`
- `task_id`

The authenticated/current user id is returned as `restored_by_user_id`.
The response also includes `audit_summary`.

The current persistence model stores durable restore context through existing
fields where possible:

- `created_from_task_id`
- `change_summary`
- copied plan snapshot metadata

No destructive schema migration is introduced in R4.

## Safer confirmation UX

The frontend restore panel now requires three deliberate inputs before enabling
restore:

1. type `RESTORE`;
2. type the selected target version id;
3. enter a restore reason of at least 8 characters.

The restore request sends only audit metadata and identifiers. It does not send
an explicit presentation plan payload.

## Validation rules

Backend validation rejects:

- confirmation values other than exact `RESTORE`;
- mismatched `confirmation_target_version_id`;
- restore reasons shorter than 8 characters when provided;
- change summaries shorter than 8 characters when provided.

## Non-goals

R4 does not add:

- destructive rollback;
- deletion of historical versions;
- branch/DAG version editor;
- collaborative conflict resolution;
- auth/RBAC redesign;
- database schema migration.
