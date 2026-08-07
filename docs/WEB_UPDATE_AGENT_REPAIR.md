# Web update agent repair

If the Operations Dashboard shows:

```text
LXC update agent control directory is not writable
```

or:

```text
LXC update agent is not installed
```

the backend can see `/control`, but the LXC-side update agent has not been
installed correctly or the bind-mounted directory is owned by root.

The backend runs as UID/GID `10001:10001`. The repair process therefore makes:

```text
/var/lib/mailhub-control -> owner 10001:10001, mode 0770
```

and mounts it into the backend as:

```text
/control
```

## Existing LXC

Run as root inside the LXC:

```bash
cd /opt/mail-attachment-hub
chmod +x scripts/repair-update-agent.sh
./scripts/repair-update-agent.sh
```

Expected output includes:

```text
Writable: True
Backend write test: OK
Watcher: active
```

Then refresh **Operations Dashboard** and click **Kontrollera GitHub**.

## Diagnostics

```bash
stat -c '%u:%g %a %n' /var/lib/mailhub-control
systemctl status mailhub-update-agent.path
cat /var/lib/mailhub-control/status.json | jq .
```

From the backend:

```bash
docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  exec backend \
  sh -c 'id; ls -ldn /control; test -w /control && echo writable'
```
