# Apply Commit 002B

Commit message:

```text
feat(core): add centralized API error handling
```

This is an overlay package. Copy it over the repository without deleting
existing files or the `.git` directory.

## Windows PowerShell

```powershell
$Source = "C:\Temp\mail-attachment-hub-commit-002B-errors"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git status
```

## Test

```powershell
docker compose --env-file .env -f compose.yml build backend

docker compose --env-file .env -f compose.yml run --rm --no-deps `
  --entrypoint sh backend `
  -c "pip install --no-cache-dir '.[test]' >/dev/null && pytest"
```

## Commit

```powershell
git add -A
git commit -m "feat(core): add centralized API error handling"
git push origin main
```
