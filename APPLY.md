# Apply complete LXC installer fix

Copy these files over the repository:

- `proxmox/install.sh`
- `compose.yml`
- `.env.example`

## Windows PowerShell

```powershell
$Source = "C:\Temp\mail-attachment-hub-lxc-installer-complete-fix"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git add proxmox/install.sh compose.yml .env.example
git commit -m "fix(installer): make LXC installation complete reliably"
git push origin main
```

## Verify GitHub file

```bash
curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)" |
  grep "Kontroll %02d/90"
```

## Clean installation

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true

bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)")"
```
