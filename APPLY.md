# Apply installer update-agent fix

Copy the files over the repository root.

## Commit

```powershell
git add proxmox/install.sh scripts/install-update-agent.sh scripts/update-agent.sh scripts/lxc-update.sh
git commit -m "fix(installer): install update agent before Docker startup"
git push origin main
```

## Clean reinstall

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true

bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?$(date +%s)")"
```

During installation you should now see:

```text
Installing MailHub Update Agent
Update agent status:
enabled
active
```

and later:

```text
Verifying MailHub Update Agent
Update agent control directory: writable
```
