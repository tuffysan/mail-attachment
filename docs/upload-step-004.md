# Upload Step 004 on Windows 11

This package is a complete repository snapshot. Keep the existing `.git` directory and replace everything else.

```powershell
$Source = "C:\Temp\mail-attachment-hub-step-004"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Repo -Force |
    Where-Object { $_.Name -ne ".git" } |
    Remove-Item -Recurse -Force

Get-ChildItem $Source -Force |
    Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git add -A
git status
git commit -m "feat: add async database layer and Alembic migrations"
git push origin main
```
