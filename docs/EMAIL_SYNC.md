# Email Sync – Part 5D

Part 5D adds per-account synchronization control and history.

## Per-account schedule

Each email account can optionally override the global `SYNC_INTERVAL_SECONDS`.

Allowed UI presets:

- 1 minute
- 5 minutes
- 15 minutes
- 30 minutes
- 1 hour
- 6 hours
- 12 hours
- 24 hours
- global default

The database stores the override in:

```text
email_accounts.sync_interval_seconds
```

Migration:

```text
0009_email_sync_schedule.py
```

A null value means that the account continues to use the global worker interval.

## Worker behavior

The worker wakes at least once per minute and only synchronizes accounts that
are due. Accounts that have never synchronized are due immediately.

Retries continue to use the existing global retry settings.

## API

```text
PUT  /api/v1/email-accounts/{id}/schedule
GET  /api/v1/email-accounts/{id}/sync-runs
POST /api/v1/email-accounts/{id}/sync
POST /api/v1/email-accounts/{id}/sync/retry
```

The sync response now includes the run ID, attempt, messages seen, messages
created and attachments created.

## Frontend

Email Accounts now provides:

- per-account auto-sync interval;
- pause/resume automatic sync;
- last successful sync timestamp;
- manual "Synka nu";
- expandable sync history;
- attempt number and counters;
- error text for failed runs;
- "Försök igen" on failed history entries.

## Migration on existing installation

The normal backend entrypoint runs Alembic migrations. After deploying Part 5D,
migration `0009` adds the nullable schedule column without changing existing
account behavior.
