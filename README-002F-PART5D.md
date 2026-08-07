# Commit 002F – Part 5D
## Email sync improvements

Apply after Parts 5A–5C.

### Features

- per-account automatic sync interval;
- pause/resume automatic sync;
- sync history per email account;
- richer manual-sync results;
- retry action for failed sync runs;
- worker only syncs accounts that are actually due;
- newly configured accounts sync immediately;
- existing global `SYNC_INTERVAL_SECONDS` remains the fallback.

### Database

Adds Alembic migration:

```text
0009_email_sync_schedule.py
```

with nullable:

```text
email_accounts.sync_interval_seconds
```

Existing accounts therefore retain current behavior.

### Verification

```text
schedule regression tests             PASS
frontend TypeScript                   PASS
focused backend regression suite      PASS
migration/API/worker static checks    PASS
```

### Apply

```powershell
git add backend/alembic/versions/0009_email_sync_schedule.py `
        backend/src/mailhub/db/models.py `
        backend/src/mailhub/mail/schemas.py `
        backend/src/mailhub/mail/schedule.py `
        backend/src/mailhub/api/email_accounts.py `
        backend/src/mailhub/api/mail_engine.py `
        backend/src/mailhub/worker.py `
        backend/tests/test_mail_schedule.py `
        frontend/src/types.ts `
        frontend/src/api.ts `
        frontend/src/pages/EmailAccountsPage.tsx `
        frontend/src/styles.css `
        docs/EMAIL_SYNC.md

git commit -m "feat(mail): add per-account scheduling and sync history"
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
  up -d --build backend worker frontend

mailhub doctor
```

The backend entrypoint applies migration `0009` automatically.
