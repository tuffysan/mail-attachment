# Mail Attachment Hub - Complete Update Agent Fix

This package fixes the LXC web update agent and `/control` permissions.

## Replace / add these files in the repository

Copy the package contents over the repository root.

Then commit:

```powershell
git add -A
git commit -m "fix(update): install and repair LXC web update agent"
git push origin main
```

## Clean reinstall

On the Proxmox host:

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true

bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)")"
```

## Existing LXC repair

Inside the LXC:

```bash
cd /opt/mail-attachment-hub
git pull --ff-only origin main
chmod +x scripts/fix-mailhub-update-agent-lxc.sh
./scripts/fix-mailhub-update-agent-lxc.sh
```

Expected:

```text
owner=10001:10001
mode=770
Writable: True
Backend write test: OK
mailhub-update-agent.path: active
```
