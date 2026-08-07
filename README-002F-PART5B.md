# Commit 002F – Part 5B
## Backup & Restore UI

Apply on top of:

1. `mail-attachment-hub-commit-002F-final.zip`
2. `mail-attachment-hub-002F-part5A-ci.zip`

### Features

- Create application backup from the web UI.
- Backup history with size/details.
- Restore a selected backup from the web UI.
- Exact confirmation phrase required before restore.
- Automatic pre-restore safety backup.
- SHA-256 verification before restore.
- PostgreSQL, attachments, routed files and matching application encryption
  environment are restored together.
- Current PostgreSQL credentials, Docker Compose project identity and exposed
  frontend/API ports are preserved during restore.
- Backup/restore operations run through the privileged LXC agent; the backend
  container is not given Docker/root access.

### Backup location

```text
/var/backups/mailhub
```

### New API

```text
GET  /api/v1/admin/backups
POST /api/v1/admin/backups/refresh
POST /api/v1/admin/backups
POST /api/v1/admin/backups/restore
```

Restore requires:

```json
{
  "backup_id": "mailhub-...",
  "confirmation": "RESTORE mailhub-..."
}
```

### Verification performed

```text
Frontend TypeScript                    PASS
Backend focused suite + 5B tests       PASS
Backup/restore shell regression        PASS
All changed shell scripts bash -n      PASS
Release self-test                      PASS
```

The actual PostgreSQL/Docker volume restore must run in the real LXC. The
packaging environment cannot emulate your nested Proxmox/Docker runtime.

### Apply

```powershell
git add backend/src/mailhub/maintenance_control.py `
        backend/src/mailhub/api/backups.py `
        backend/src/mailhub/main.py `
        backend/src/mailhub/update_control.py `
        backend/tests/test_maintenance_control.py `
        frontend/src/api.ts `
        frontend/src/types.ts `
        frontend/src/App.tsx `
        frontend/src/pages/BackupsPage.tsx `
        frontend/src/pages/DashboardPage.tsx `
        frontend/src/pages/AdminPage.tsx `
        frontend/src/styles.css `
        scripts/backup.sh `
        scripts/restore.sh `
        scripts/update-agent.sh `
        scripts/install-update-agent.sh `
        scripts/test-backup-restore-platform.sh `
        scripts/release-self-test.sh `
        proxmox/install.sh `
        docs/BACKUP_RESTORE.md

git update-index --chmod=+x scripts/backup.sh
git update-index --chmod=+x scripts/restore.sh
git update-index --chmod=+x scripts/update-agent.sh
git update-index --chmod=+x scripts/install-update-agent.sh
git update-index --chmod=+x scripts/test-backup-restore-platform.sh
git update-index --chmod=+x scripts/release-self-test.sh
git update-index --chmod=+x proxmox/install.sh

git commit -m "feat(backups): add web backup and safe restore"
git push origin main
```

### Existing LXC

After pushing and updating the LXC, reinstall/repair the agent so the new
maintenance control files are initialized:

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x scripts/install-update-agent.sh
./scripts/install-update-agent.sh

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --build backend frontend

mailhub doctor
```

Then open:

```text
http://<LXC-IP>:3000/admin/backups
```
