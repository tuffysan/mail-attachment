# Web updates for Proxmox LXC

Administrators can check GitHub and start an LXC update from the Operations
Dashboard.

## Security design

The backend container does not receive the Docker socket and does not run as
root.

Instead:

1. the backend writes a small request file to `/control`;
2. `/control` is mapped to `/var/lib/mailhub-control` on the LXC host;
3. a systemd path unit notices the request;
4. the root-owned update agent performs Git and Docker operations;
5. the update agent writes status JSON back to the control directory.

Only authenticated administrators can use the update API.

## Install on an existing LXC

After pushing the feature to GitHub, first update the source manually:

```bash
pct enter <CTID>

cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x scripts/install-update-agent.sh
./scripts/install-update-agent.sh

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --build
```

Then open:

```text
Administration / Operations Dashboard
```

The **GitHub-uppdatering** panel can check and install future updates.

## Update logs

```bash
cat /var/lib/mailhub-control/update.log
```

Agent status:

```bash
cat /var/lib/mailhub-control/status.json | jq .
```

Systemd status:

```bash
systemctl status mailhub-update-agent.path
systemctl status mailhub-update-agent.service
```
