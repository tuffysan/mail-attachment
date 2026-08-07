# Apply Web Update Manager

Copy the overlay over the repository.

## Commit

```powershell
git add backend frontend scripts compose.yml docs/WEB_UPDATES.md
git commit -m "feat(operations): add web-based LXC updates"
git push origin main
```

## One-time activation on an existing LXC

The web update feature cannot update itself before the host-side agent has been
installed. Run this once:

```bash
pct enter 134

cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x scripts/install-update-agent.sh scripts/update-agent.sh scripts/lxc-update.sh
./scripts/install-update-agent.sh

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --build
```

Reload the browser with Ctrl+F5 and open the Operations Dashboard.

From then on, future GitHub changes can be installed from the web interface.
