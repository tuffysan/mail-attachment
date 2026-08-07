# Commit 002F – Part 2B
## Setup Wizard + Dashboard + navigation polish

Apply after Part 2A.

### Setup Guard

Backend/setup-status failures are no longer treated as "setup completed".

Previously:

```text
getSetupStatus() fails -> state = ready
```

That could let the UI continue when backend status was unavailable.

Now the guard enters a dedicated error state and offers **Försök igen**. The
application only proceeds after backend confirms whether first setup is complete.

### Setup Wizard

Step 2 now uses the Part 1C validation API before an IMAP account is saved.

The wizard adds:

- **Testa anslutning**
- successful connection summary
- save button enabled only after successful validation
- automatic invalidation if email, password or IMAP host changes
- clearer handling when an email account already exists
- clearer first-boot summary
- explicit next steps after installation

The wizard still allows the email step to be skipped. Google OAuth can then be
configured from the main UI after first setup.

### Dashboard

The overview now includes clear quick-action cards:

- E-postkonton
- Regler
- Lagring
- Google OAuth (admin)
- Operations (admin)

System status can be refreshed manually without reloading the page.

User-loading errors and health/readiness errors are tracked independently, so
one does not overwrite the other.

### Verification

The actual Part 2A + Part 2B frontend tree was checked with:

```text
tsc -p tsconfig.json --noEmit
```

Result:

```text
exit code 0
```

A named import/export consistency check also passed.

### Apply

```powershell
git add frontend/src/components/SetupGuard.tsx `
        frontend/src/pages/SetupWizardPage.tsx `
        frontend/src/pages/DashboardPage.tsx `
        frontend/src/styles.css

git commit -m "fix(frontend): harden setup flow and dashboard navigation"
git push origin main
```

### Rebuild frontend in LXC

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
