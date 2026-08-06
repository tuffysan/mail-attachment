# Apply Commit 002A

Commit message:

`feat(core): add structured logging and request middleware`

This is an overlay package. Do not delete the repository and do not delete `.git`.

## Windows PowerShell

```powershell
$Source = "C:\Temp\mail-attachment-hub-commit-002A-observability"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git status
```

## Validate

```powershell
docker compose --env-file .env -f compose.yml build backend

docker compose --env-file .env -f compose.yml run --rm --no-deps `
  --entrypoint sh backend `
  -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest"
```

Then run the stack and verify headers:

```powershell
docker compose --env-file .env -f compose.yml up -d --build
Invoke-WebRequest http://127.0.0.1:8080/health/live | Select-Object -ExpandProperty Headers
```

## Commit

```powershell
git add .env.example compose.yml `
  backend/src/mailhub/core/config/settings.py `
  backend/src/mailhub/core/middleware `
  backend/src/mailhub/core/observability `
  backend/src/mailhub/logging_config.py `
  backend/src/mailhub/main.py `
  backend/tests/test_middleware.py `
  backend/tests/test_observability.py `
  docs/OBSERVABILITY.md

git commit -m "feat(core): add structured logging and request middleware"
git push origin main
```
