# Lägg in den korrigerade Proxmox-installern

## Kopiera filerna

```powershell
$Source = "C:\Temp\mail-attachment-hub-proxmox-installer-fixed"
$Repo   = "C:\Git\mail-attachment"

Get-ChildItem $Source -Force |
    Where-Object { $_.Name -ne "APPLY.md" } |
    Copy-Item -Destination $Repo -Recurse -Force

Set-Location $Repo
git status
```

## Commit

```powershell
git add proxmox/install.sh docs/PROXMOX_INSTALLATION.md
git commit -m "fix(installer): correct Proxmox template selection"
git push origin main
```

## Ta bort den misslyckade containern

Kör på Proxmox:

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true
```

## Installera igen

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh)"
```
