# Commit 002F – Part 1D
## Google OAuth backend hardening

Apply after Part 1A, Part 1B and Part 1C.

### Changes

1. **OAuth provider whitelist**
   - Only `google` and `microsoft` are accepted.
   - Provider names are normalized case-insensitively.
   - Unknown providers are rejected before any token or database work.

2. **Safer OAuth callback handling**
   - Explicit handling for OAuth `error` and `error_description`.
   - Missing `code` or `state` now returns a clear client error.
   - Provider validation is centralized in `validate_oauth_callback()`.

3. **Google identity hardening**
   - Explicitly rejects an unverified Google email address.
   - Access-token expiry parsing is tolerant of malformed provider values.

4. **Google Client ID validation**
   - Trims surrounding whitespace.
   - Rejects embedded whitespace.
   - Requires `.apps.googleusercontent.com`.

5. **OAuth Base URL validation**
   - Rejects user/password components.
   - Rejects query strings and fragments.
   - Keeps the existing HTTPS/localhost/raw-IP safety rules.

6. **Encrypted Client Secret recovery**
   - If a stored Google Client Secret cannot be decrypted, the API now returns
     an actionable configuration error instead of an unexpected backend 500.
   - Administrator can re-save OAuth configuration.

7. **Provider-specific authorization parameters**
   - Google-only parameters such as `access_type=offline`, `prompt=consent`,
     and `include_granted_scopes=true` are no longer sent to Microsoft.

### Tests

Focused OAuth regression suite:

```text
tests/test_oauth_settings.py
tests/test_oauth_hardening.py

18 passed
```

The local runner logs an unrelated spreadsheet-runtime warmup warning after
pytest, but pytest exits with status 0 and all OAuth tests pass.

### Apply

```powershell
git add backend/src/mailhub/api/mail_engine.py `
        backend/src/mailhub/api/oauth_admin.py `
        backend/src/mailhub/mail/oauth.py `
        backend/src/mailhub/mail/oauth_settings.py `
        backend/tests/test_oauth_hardening.py

git commit -m "fix(oauth): harden Google OAuth configuration and callback flow"
git push origin main
```

### Update existing LXC

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --build backend worker
```

No Alembic migration is required by Part 1D.
