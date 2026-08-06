# First Boot Wizard

After the Proxmox or Docker installer starts Mail Attachment Hub, sign in
using the generated administrator credentials. If setup has not been
completed, the application redirects automatically to `/setup`.

## Wizard steps

1. Administrator display name, language and timezone
2. Optional administrator password change
3. Optional first IMAP account
4. First local storage destination
5. Optional first attachment rule and final confirmation

Email and rules may be skipped and configured later. A local storage
destination is reused when the database migration already created one.

## Setup status

Public endpoint:

```text
GET /api/v1/setup/status
```

Authenticated administrator endpoints:

```text
PUT  /api/v1/setup/preferences
POST /api/v1/setup/password
POST /api/v1/setup/complete
```

The completion state, language and timezone are stored in the existing
`system_metadata` table, so no additional database migration is required.

## Resetting the wizard

To reopen the wizard, update `setup.completed` to `false` in
`system_metadata`:

```bash
docker compose --env-file .env -f compose.yml exec postgres       psql -U mailhub -d mailhub       -c "UPDATE system_metadata SET value='false' WHERE key='setup.completed';"
```

Reopen the web UI and log in again.
