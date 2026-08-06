# Configuration

Mail Attachment Hub loads configuration from environment variables and an
optional `.env` file using Pydantic Settings.

## Compatibility

Existing code may continue importing:

```python
from mailhub.config import Settings, get_settings
```

New code should prefer:

```python
from mailhub.core.config import Settings, get_settings
```

Flat attributes such as `settings.database_url` remain supported. New code
may use typed grouped views:

```python
settings.database.url
settings.security.secret_key
settings.mail.sync_interval_seconds
settings.oauth.google_client_id
settings.storage.retry_attempts
```

## Startup validation

The application validates:

- supported application environments;
- HTTP/HTTPS base URL;
- async database driver;
- Redis URL;
- log level;
- secret length;
- timing and size limits;
- OAuth client ID/secret pairs;
- placeholder secrets in production.

Invalid configuration stops the application at startup with a clear error.

## Required secrets

`APP_SECRET_KEY` must be at least 32 characters and must remain unchanged
after encrypted credentials have been saved.

`ADMIN_PASSWORD` must be at least 12 characters when provided.

## OAuth

Google OAuth requires both:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Microsoft OAuth requires both:

- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`

Empty optional OAuth values are normalized to `None`.

## Testing

Run:

```bash
docker compose --env-file .env -f compose.yml run --rm --no-deps       --entrypoint sh backend       -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest"
```
