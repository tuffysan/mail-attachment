# Lifecycle and workers

Commit 002D introduces cooperative shutdown and process-local worker status.

## Graceful shutdown

Both API and worker processes use a shared lifecycle manager. Shutdown hooks
execute in reverse registration order and each hook is bounded by
`SHUTDOWN_TIMEOUT_SECONDS`.

The API marks itself unready before resources are closed. The worker stops
accepting new mailbox work, finishes its current operation where possible,
closes database connections and reports a final stopped state.

## Worker status

The worker registry records:

- state: starting, running, idle, stopping, stopped or failed;
- startup and heartbeat timestamps;
- latest activity;
- completed cycles;
- failure count;
- safe exception type for the latest failure.

Exception messages are not exposed through worker status.

## Administration endpoints

Authenticated administrators can use:

- `GET /api/v1/system/status`
- `GET /api/v1/system/workers`
- `POST /api/v1/system/shutdown`

The shutdown endpoint sends SIGTERM to the API process after registering the
shutdown request. Container orchestration should normally remain the primary
way to stop services.

## Limitation

The API and worker run in separate containers, so their in-memory registries
are process-local. A future commit can persist heartbeats in Redis to expose
cross-container worker state from the API.
