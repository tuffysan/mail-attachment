# Observability and HTTP request context

Commit 002A adds dependency-free structured logging and HTTP middleware.

## Log formats

`LOG_FORMAT=json` is recommended for Docker and production. Each line contains
UTC timestamp, level, logger, message, request context and serializable extra
fields. Use `LOG_FORMAT=console` for readable local development output.

## Request context

Every HTTP response receives:

- `X-Request-ID`
- `X-Correlation-ID`

Valid incoming identifiers are preserved. Invalid or missing values are replaced
with UUIDs. Application logs created during a request automatically include both
identifiers through Python context variables.

## Access logs

One `http_request_completed` event is emitted after each request with method,
path, status, duration and client IP. Health endpoints are excluded by default.
Configure exclusions with `REQUEST_LOG_EXCLUDED_PATHS`.

## Security headers

The backend applies CSP, frame protection, MIME sniffing protection, referrer
policy and browser permissions policy. Set `SECURITY_HEADERS_ENABLED=false` only
for controlled troubleshooting.

## Testing

```bash
docker compose --env-file .env -f compose.yml build backend
docker compose --env-file .env -f compose.yml run --rm --no-deps \
  --entrypoint sh backend \
  -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest backend/tests/test_observability.py backend/tests/test_middleware.py"
```
