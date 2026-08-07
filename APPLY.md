# Dashboard health fix

This overlay fixes a frontend bug where `/health/ready` returning HTTP 503
for a degraded dependency was incorrectly treated as a backend connection
failure.

## Copy

```powershell
$Source = "C:\Temp\mail-attachment-hub-dashboard-health-fix"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git add frontend/src/api.ts frontend/src/pages/DashboardPage.tsx
git commit -m "fix(frontend): render degraded backend readiness"
git push origin main
```

## Update existing LXC

```bash
pct exec 134 -- bash -lc '
cd /opt/mail-attachment-hub
git pull --ff-only origin main
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml build frontend
docker compose --env-file .env -f compose.yml -f compose.override.lxc.yml up -d frontend
'
```

Then reload the web page with Ctrl+F5.
