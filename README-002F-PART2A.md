# Commit 002F – Part 2A
## Frontend stabilization

Apply after backend Parts 1A–1E.

### Email Accounts

The frontend now uses the Part 1C endpoint:

```text
POST /api/v1/email-accounts/validate
```

A password/IMAP account can therefore be tested before it is stored.

The page adds:

- **Testa inställningar**
- validation result before saving;
- **Spara verifierat konto** after a successful test;
- automatic invalidation of the previous test result when form values change;
- OAuth account/provider information in the account list;
- success notification when returning from Google OAuth.

`EmailAccount` types now include `auth_type` and `oauth_provider`, matching the
Part 1C backend response.

### Google OAuth

- Removes an unused router dependency.
- Callback URL copy now handles browser clipboard failures cleanly.
- Existing direct links to Google Auth Platform, Gmail API and OAuth Clients
  remain available.

### Operations Dashboard / GitHub Update

Opening Operations Dashboard no longer automatically triggers a GitHub fetch.
It reads current update status first; the administrator explicitly selects
**Kontrollera GitHub**.

The panel distinguishes the initial **Redo** state from **Ej installerad** and
gives a clearer `/control` diagnostic if the LXC update agent is unavailable.

### Storage

- Failed storage tests now use the failed status style.
- Local permissions also show whether the directory is executable/traversable.

### Verification performed

All modified `.ts` / `.tsx` files were parsed and transpiled successfully using
TypeScript.

A static named import/export check was run against `api.ts` and `types.ts` to
prevent the previous class of build errors where a page referenced a missing
export.

A complete `npm run build` could not be run in the packaging environment
because its internal npm registry returns HTTP 404 for
`@types/react@19.1.10`. That dependency is already declared in the project.

### Apply

```powershell
git add frontend/src/api.ts `
        frontend/src/types.ts `
        frontend/src/pages/EmailAccountsPage.tsx `
        frontend/src/pages/GoogleOAuthSetupPage.tsx `
        frontend/src/pages/StoragePage.tsx `
        frontend/src/pages/AdminPage.tsx `
        frontend/src/styles.css

git commit -m "fix(frontend): stabilize mail OAuth storage and updates"
git push origin main
```

### Rebuild LXC frontend

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
