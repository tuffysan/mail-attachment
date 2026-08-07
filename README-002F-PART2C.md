# Commit 002F – Part 2C
## Rules + Storage UX + frontend integration

Apply after Parts 2A and 2B.

### Rules

The rule editor now has client-side validation for:

- rule name;
- folder template;
- at least one destination;
- regular expressions;
- minimum/maximum file size.

The page now exposes the previously hidden recipient filter.

Rule simulation no longer uses a fixed hardcoded example only. The user can
enter:

- sender;
- recipients;
- subject;
- filename;
- content type;
- size.

The simulation is read-only and evaluates currently active rules.

Rule deletion now requires confirmation and reports backend errors cleanly.

The rule list also shows active/inactive state and stop-after-match behavior.

### Storage

New storage destinations are now:

1. saved;
2. tested immediately;
3. shown with the actual connection-test result.

If saving succeeds but the connection test fails, the UI makes that distinction
clear.

Local destinations require a non-empty path.

Storage deletion now requires confirmation and handles API errors.

The local permissions panel displays a warning when the path is not writable or
traversable.

Empty-state UI was added for installations with no storage destinations.

### Verification

The complete frontend tree containing Parts 2A + 2B + 2C was validated with:

```text
tsc -p tsconfig.json --noEmit
```

Result:

```text
exit code 0
```

Named API/type imports were also verified against the exports in `api.ts` and
`types.ts`.

### Apply

```powershell
git add frontend/src/pages/RulesPage.tsx `
        frontend/src/pages/StoragePage.tsx `
        frontend/src/styles.css

git commit -m "fix(frontend): improve rules simulation and storage workflow"
git push origin main
```

### Rebuild frontend

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
