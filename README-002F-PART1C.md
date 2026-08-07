# Commit 002F – Part 1C
## Email Accounts / IMAP / OAuth backend stabilization

Apply after Part 1A and Part 1B.

### Changes

1. **IMAP connection tests now support OAuth/XOAUTH2**
   - Password authentication still uses IMAP LOGIN.
   - OAuth accounts authenticate with XOAUTH2.
   - A missing credential produces a controlled validation error.

2. **Shared credential resolver**
   - New `mailhub.mail.credentials.resolve_mail_credential`.
   - Password decryption and OAuth token refresh now use the same implementation
     for both manual connection tests and background synchronization.
   - Fresh OAuth access tokens are reused.
   - Expired tokens are refreshed and encrypted back into the account.

3. **OAuth accounts can now use the existing Test button**
   - Previously `/email-accounts/{id}/test` always attempted to decrypt
     `encrypted_password`, which is null for OAuth accounts.
   - The endpoint now branches correctly through the shared credential resolver.

4. **Pre-save IMAP validation API**
   - New endpoint:
     `POST /api/v1/email-accounts/validate`
   - Allows the frontend/setup wizard to verify ordinary IMAP credentials
     without persisting them first.

5. **Email account API reports authentication type**
   - Responses now include:
     - `auth_type`
     - `oauth_provider`
   - This is additive and does not expose credentials.

6. **Password account safety**
   - Password-created accounts explicitly set `auth_type=password`.
   - OAuth accounts cannot be edited through the password-account PATCH API.

7. **Google refresh-token guard**
   - A brand-new Google account is not saved if Google fails to return a
     refresh token.
   - Existing connected Google accounts retain their previously stored refresh
     token when Google only returns a new access token.

### Tests

Focused backend regression suite:

```text
tests/test_imap_client.py
tests/test_mail_credentials.py
tests/test_mail_crypto.py
tests/test_mail_engine.py
tests/test_oauth_settings.py

15 passed
```

### Apply

```powershell
git add backend/src/mailhub/api/email_accounts.py `
        backend/src/mailhub/api/mail_engine.py `
        backend/src/mailhub/mail/credentials.py `
        backend/src/mailhub/mail/imap_client.py `
        backend/src/mailhub/mail/schemas.py `
        backend/src/mailhub/mail/sync.py `
        backend/tests/test_imap_client.py `
        backend/tests/test_mail_credentials.py

git commit -m "fix(mail): stabilize IMAP and OAuth account credentials"
git push origin main
```

### Rebuild existing LXC

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

No Alembic migration is required by Part 1C.
