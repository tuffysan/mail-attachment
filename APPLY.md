# Apply Commit 001

This ZIP contains complete replacement and new files for:

`feat(core): redesign configuration system`

## Windows PowerShell

Extract this ZIP. From the extracted directory, copy its contents over your
cloned repository while preserving the repository's `.git` directory:

```powershell
$Source = "C:\Temp\mail-attachment-hub-commit-001-config"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git status
```

Then test and commit:

```powershell
docker compose --env-file .env -f compose.yml build backend
docker compose --env-file .env -f compose.yml run --rm --no-deps `
  --entrypoint sh backend `
  -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest"

git add backend/src/mailhub/config.py `
        backend/src/mailhub/core `
        backend/tests/test_settings.py `
        docs/CONFIGURATION.md

git commit -m "feat(core): redesign configuration system"
git push origin main
```

## Important

This is an overlay package. Do not delete other repository files and do not
delete `.git`.
