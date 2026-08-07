# Apply storage owner fix

Copy the files to the repository and push them.

```powershell
git add compose.override.lxc.yml scripts/fix-storage-permissions.sh scripts/storage-permissions-status.sh docs/STORAGE_PERMISSION_REPAIR.md
git commit -m "fix(storage): initialize local volume ownership for mailhub user"
git push origin main
```

## Repair existing LXC 134

```bash
pct enter 134

cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x scripts/fix-storage-permissions.sh
chmod +x scripts/storage-permissions-status.sh

./scripts/fix-storage-permissions.sh
```

Then reload the web application and test **Local routed files**.

## Future starts and updates

Use both compose files:

```bash
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d
```

The `storage-init` service will run before backend/worker and ensure the named
volumes are owned by UID/GID 10001.
