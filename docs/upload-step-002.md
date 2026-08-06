# Upload Step 002 to GitHub

This package completely replaces the repository working tree for Sprint 0, Step 002.
Preserve `.git`, but remove everything else before copying these files. This is required to remove the legacy prototype.

## Linux, macOS or WSL

```bash
rsync -a --delete --exclude='.git' mail-attachment-hub-step-002-clean/ mail-attachment-hub/
cd mail-attachment-hub
make check
git add -A
git commit -m "chore: establish clean Sprint 0 Step 002 infrastructure"
git push origin main
```

## Windows PowerShell

```powershell
$source = Resolve-Path ".\mail-attachment-hub-step-002-clean"
$repo = Resolve-Path ".\mail-attachment-hub"
Get-ChildItem $repo -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
Copy-Item "$source\*" $repo -Recurse -Force
Copy-Item "$source\.github" $repo -Recurse -Force
Copy-Item "$source\.editorconfig" $repo -Force
Copy-Item "$source\.env.example" $repo -Force
Copy-Item "$source\.gitignore" $repo -Force
Set-Location $repo
git add -A
git commit -m "chore: establish clean Sprint 0 Step 002 infrastructure"
git push origin main
```

## Verify from a fresh clone

```bash
git clone https://github.com/tuffysan/mail-attachment-hub.git verify-mailhub
cd verify-mailhub
make check
make init
docker compose --env-file .env -f compose.yml config --quiet
```
