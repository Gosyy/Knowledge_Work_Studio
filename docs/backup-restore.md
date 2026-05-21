# Backup and restore drill

R5 provides a safe operator drill for local/offline KW Studio deployments.

## Safety rules

- Backup helper scripts are dry-run only in R5.
- Restore checks are dry-run only in R5.
- Scripts must not print secret values.
- Restore checks must not write to Postgres.
- Restore checks must not mutate Docker volumes.
- Restore checks must not extract artifact archives by default.

## Backup assets

A complete local deployment backup should include:

1. a Postgres custom-format dump;
2. a read-only archive of the `kw_storage` artifact volume;
3. checksums for backup files;
4. the exact Git commit and deployment documentation used for the deployment.

## Generate backup command hints

```bash
python3 scripts/kw_operator_backup.py \
  --repo-root . \
  --dry-run \
  --timestamp 20260430T120000Z
```

The script prints command hints but does not run them.

## Generate restore-check command hints

```bash
python3 scripts/kw_operator_restore_check.py \
  --repo-root . \
  --dry-run \
  --backup-dir backups/20260430T120000Z
```

To require the expected backup files to exist:

```bash
python3 scripts/kw_operator_restore_check.py \
  --repo-root . \
  --dry-run \
  --backup-dir backups/20260430T120000Z \
  --require-files
```

## Manual restore policy

R5 intentionally does not automate destructive restore. A future accepted issue may
add an operator-approved restore path, but it must remain explicit, documented,
and protected from accidental execution.

Before any manual restore, an operator must verify:

- target environment is not production unless explicitly approved;
- backup files pass checksum validation;
- Postgres dump catalog can be listed with `pg_restore --list`;
- artifact archive can be listed with `tar -tzf`;
- current deployment state has been backed up separately;
- rollback procedure is written before restore begins.
