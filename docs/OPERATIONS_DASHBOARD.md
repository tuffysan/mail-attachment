# Operations Dashboard

The Operations Dashboard is available to administrators at `/admin`.

It aggregates existing application data without adding a database migration.

## Dashboard sections

- account, message and attachment counters;
- successful, pending and failed routing executions;
- PostgreSQL, Redis and attachment-storage health;
- process-local worker heartbeat and cycle state;
- configured storage destinations and their latest connection test;
- latest activity events;
- latest synchronization and routing failures.

The frontend refreshes automatically every 30 seconds and also provides a
manual refresh button.

## API

```text
GET /api/v1/operations/dashboard
```

The endpoint requires an authenticated administrator account.

## Worker visibility

Worker state is currently process-local. When API and mail worker run in
separate containers, the API may not display the worker container's registry.
Sync runs and activity events are persisted and still appear in the
operations data. Redis-based cross-process heartbeat remains a future
enhancement.
