# Apply Operations Dashboard

This is an overlay package. Copy it over the repository without deleting
existing files or `.git`.

## Windows PowerShell

```powershell
$Source = "C:\Temp\mail-attachment-hub-operations-dashboard"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git status
```

## Test

```powershell
docker compose --env-file .env -f compose.yml build backend frontend

docker compose --env-file .env -f compose.yml run --rm --no-deps `
  --entrypoint sh backend `
  -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest"

docker compose --env-file .env -f compose.yml up -d --build
```

Open `/admin` after signing in as an administrator.

## Commit

```powershell
git add -A
git commit -m "feat(operations): add administration dashboard"
git push origin main
```
