# Required Update Agent installer fix

This package makes the LXC update agent mandatory during installation.

## Copy and commit

```powershell
git add proxmox/install.sh scripts/install-update-agent.sh scripts/update-agent.sh scripts/lxc-update.sh
git update-index --chmod=+x proxmox/install.sh
git update-index --chmod=+x scripts/install-update-agent.sh
git update-index --chmod=+x scripts/update-agent.sh
git update-index --chmod=+x scripts/lxc-update.sh
git commit -m "fix(installer): require and verify LXC update agent"
git push origin main
```

## Verify GitHub before reinstalling

```bash
curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)" |
grep -E "Running scripts/install-update-agent|control owner|Update agent control directory"
```

You must see all three strings.

## Clean reinstall

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true

bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)")"
```
