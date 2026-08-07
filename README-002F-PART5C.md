# Commit 002F – Part 5C
## Better Operations Dashboard

Apply after Part 5A and Part 5B.

### Added

Operations Dashboard now shows:

- CPU count and Linux load averages
- RAM usage
- disk usage
- LXC/runtime uptime
- backup count, latest backup and total backup size
- latest email synchronization runs
- per-sync messages and attachments
- sync error details

The overall dashboard state also becomes degraded at:

```text
RAM >= 95%
disk >= 95%
backup agent state == error
```

Warning styling starts earlier in the frontend at 85%.

### Backend implementation

No new runtime package was added. System information is collected using:

```text
/proc/meminfo
/proc/uptime
os.getloadavg()
shutil.disk_usage()
```

The Operations package was also changed to lazy-load its aggregate service.
That removes an unnecessary Redis/health dependency when importing pure
operations helper modules.

### Verification

```text
Python compile                         PASS
system resource regression test       PASS
focused backend suite                 PASS
frontend TypeScript                    PASS
```

### Apply

```powershell
git add backend/src/mailhub/operations `
        backend/tests/test_operations_system_resources.py `
        frontend/src/types.ts `
        frontend/src/pages/AdminPage.tsx `
        frontend/src/styles.css `
        docs/OPERATIONS_DASHBOARD.md

git commit -m "feat(operations): add resources backups and sync history"
git push origin main
```

### Existing LXC

After the commit is on GitHub:

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

Then open:

```text
http://<LXC-IP>:3000/admin
```
