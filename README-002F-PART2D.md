# Commit 002F – Part 2D
## Operations Dashboard + GitHub Update UX + frontend final integration

Apply after Parts 2A–2C.

### GitHub Update

- The dashboard polls update status every 2 seconds only while a check or update
  is actually running.
- Idle pages no longer perform constant 3-second update polling.
- Starting a GitHub check schedules a status refresh.
- Starting an update schedules both status and operations refreshes.
- Update state labels are centralized.
- A failed status read clears stale status instead of leaving old data visible.
- The `error` state points administrators to:
  `/var/lib/mailhub-control/update.log`.
- The `unavailable` state keeps the `/control` diagnostic.

### API error handling

Backend error payloads are now accepted as `Error.message` only when `detail`
is actually a string. Unexpected JSON error shapes fall back to the generic
message instead of producing invalid UI errors.

### Verification

The reconstructed frontend containing Parts 2A + 2B + 2C + 2D was checked with:

```text
tsc -p tsconfig.json --noEmit
```

Result:

```text
exit code 0
```

### Apply

```powershell
git add frontend/src/pages/AdminPage.tsx `
        frontend/src/api.ts `
        frontend/src/styles.css

git commit -m "fix(frontend): harden operations update workflow"
git push origin main
```

### Rebuild

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  build frontend

docker compose \
  --env-file .env \
  -f compose.yml \
  -f compose.override.lxc.yml \
  up -d frontend
```
