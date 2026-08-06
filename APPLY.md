# Apply First Boot Wizard

This is an overlay package. Copy its contents over the repository without
deleting existing files or `.git`.

## Windows PowerShell

```powershell
$Source = "C:\Temp\mail-attachment-hub-first-boot-wizard"
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

Open `http://SERVER-IP:3000`, sign in with the generated credentials and
complete the wizard.

## Commit

```powershell
git add -A
git commit -m "feat(setup): add first boot configuration wizard"
git push origin main
```
