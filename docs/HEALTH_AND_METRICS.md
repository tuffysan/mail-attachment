# Health checks and metrics

Commit 002C adds explicit startup, liveness and readiness semantics plus a
Prometheus-compatible metrics endpoint.

## Endpoints

### `GET /health/live`

Confirms that the API process is running. It does not check external
dependencies.

### `GET /health/startup`

Returns HTTP 200 after application startup has completed. During startup or
shutdown it returns HTTP 503.

### `GET /health/ready`

Returns HTTP 200 only when:

- application startup is complete;
- shutdown has not begun;
- PostgreSQL responds;
- Redis responds;
- the attachment staging directory is writable.

Each dependency includes a safe detail and latency in milliseconds.

### `GET /metrics`

Exposes Prometheus text format with:

- process uptime;
- HTTP request counts by method, route and status;
- accumulated request duration;
- duration observation count.

The endpoint intentionally avoids process-global third-party collectors, so
tests remain deterministic and the application keeps a small dependency
surface.

## Container probes

Recommended production probes:

- startup: `/health/startup`
- liveness: `/health/live`
- readiness: `/health/ready`

Do not use readiness as liveness. A temporary database outage should remove
the container from service without causing an unnecessary restart loop.
