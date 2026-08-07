# Commit 002F – Part 5E
## Security hardening

Apply after Parts 5A–5D.

### Added

- JWT token-version validation.
- Password changes invalidate all existing access tokens.
- Login rate limiting: 10 attempts per 5 minutes per remote-address/email key.
- Audit events for successful login, failed login and password changes.
- Administrator audit API.
- New `/security` web page.
- Password change UI.
- Explicit session logout.
- Alembic migration `0010_security_hardening.py`.

### Verification

```text
Python compile / static token integration   PASS
Login rate-limit tests                      PASS
Focused backend regression suite            PASS
Frontend TypeScript                         PASS
```

The local packaging runtime does not have the backend's `pwdlib` dependency
installed globally, so JWT/password integration was validated through source
compilation/static integration plus the existing application dependency
manifest. The Docker/CI backend installation installs the declared backend
dependencies before running the full suite.

### Apply

```powershell
git add backend/alembic/versions/0010_security_hardening.py `
        backend/src/mailhub/db/models.py `
        backend/src/mailhub/auth `
        backend/src/mailhub/api/auth.py `
        backend/src/mailhub/api/setup.py `
        backend/tests/test_auth_rate_limit.py `
        frontend/src/types.ts `
        frontend/src/api.ts `
        frontend/src/App.tsx `
        frontend/src/pages/SecurityPage.tsx `
        frontend/src/pages/DashboardPage.tsx `
        docs/SECURITY_HARDENING.md

git commit -m "feat(security): harden authentication and session handling"
git push origin main
```

### Existing LXC

After pushing:

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --build backend frontend

mailhub doctor
```

The backend entrypoint applies migration `0010` automatically.

Then open:

```text
http://<LXC-IP>:3000/security
```
