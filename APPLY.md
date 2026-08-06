# Apply Proxmox installer overlay

This package adds a complete one-line Proxmox LXC installer.

## Copy files

```powershell
$Source = "C:\Temp\mail-attachment-hub-proxmox-installer"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
  Where-Object { $_.Name -ne "APPLY.md" } |
  Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git status
```

## Commit

```powershell
git add proxmox docs/PROXMOX_INSTALLATION.md
git commit -m "feat(installer): add one-line Proxmox LXC appliance"
git push origin main
```

## Install after pushing

Run on the Proxmox host:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```
