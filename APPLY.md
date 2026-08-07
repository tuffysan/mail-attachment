# Apply Google OAuth Web Setup

Copy this overlay over the repository.

## Commit

```powershell
git add backend frontend docs/GOOGLE_OAUTH_SETUP.md
git commit -m "feat(oauth): configure Google OAuth from web interface"
git push origin main
```

## Update existing LXC

If web updates are working, use the Operations Dashboard.

Otherwise:

```bash
pct enter 134

cd /opt/mail-attachment-hub
git pull --ff-only origin main

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d --build
```

Reload the browser with Ctrl+F5.

Then open:

```text
E-postkonton -> Anslut Gmail med Google
```

If OAuth is not configured, the browser opens the Google OAuth setup page.
