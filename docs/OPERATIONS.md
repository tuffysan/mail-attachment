# Operations

## Backup
`make backup`

Backups contain PostgreSQL, attachment staging, routed files and a protected copy of `.env`.

## Restore
`./scripts/restore.sh backups/<directory>`

## Diagnostics
`make doctor`

## Upgrade
`./scripts/update.sh`

## Production
Set a DNS record to the server, configure `DOMAIN` and `LETSENCRYPT_EMAIL`, and run `make production-up`.

## Security checklist
- Never commit `.env`.
- Keep `APP_SECRET_KEY` unchanged.
- Expose only ports 80/443.
- Use unique OAuth applications.
- Review audit logs.
- Test backups regularly.
