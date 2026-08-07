# Apply Web Update Agent permission fix

Copy all files over the repository.

```powershell
git add scripts compose.yml proxmox/install.sh docs/WEB_UPDATE_AGENT_REPAIR.md
git commit -m "fix(update): make LXC update control directory writable"
git push origin main
```

## Repair existing LXC 134

```bash
pct enter 134

cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x scripts/repair-update-agent.sh
./scripts/repair-update-agent.sh
```

Reload the browser with Ctrl+F5 and open:

```text
Administration -> Operations Dashboard -> GitHub-uppdatering
```

Click **Kontrollera GitHub**.
