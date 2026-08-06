# Apply the systemd-based LXC installer

Copy:

- `proxmox/install.sh`
- `compose.override.lxc.yml`

Commit:

```powershell
git add proxmox/install.sh compose.override.lxc.yml
git commit -m "fix(installer): run LXC setup as monitored systemd job"
git push origin main
```

Verify the new installer:

```bash
curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)" |
  grep "systemd-run"
```

Clean installation:

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true

bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)")"
```
