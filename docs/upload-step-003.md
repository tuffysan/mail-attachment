# Upload Step 003 on Windows 11

Replace the repository contents while preserving `.git`, then commit all additions and removals.

```powershell
$Source = "C:\Temp\mail-attachment-hub-step-003"
$Repo = "C:\Git\mail-attachment"

Get-ChildItem $Repo -Force |
  Where-Object { $_.Name -ne ".git" } |
  Remove-Item -Recurse -Force

Get-ChildItem $Source -Force |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git add -A
git commit -m "feat: add FastAPI backend and health API"
git push origin master
```
