# Fix frontend build after local-storage permissions update

This overlay restores the missing frontend exports used by `StoragePage.tsx`.

## Copy to repository

```powershell
$Source = "C:\Temp\mail-attachment-hub-storage-frontend-build-fix"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo

git add frontend/src/api.ts frontend/src/types.ts frontend/src/pages/StoragePage.tsx
git commit -m "fix(frontend): restore local storage permission exports"
git push origin main
```

## Existing LXC

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  build frontend

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d frontend
```
