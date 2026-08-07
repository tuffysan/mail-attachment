# Mail Attachment Hub – Commit 002F Release Candidate (Part 4B)

This package is the complete 002F stabilization tree with final clean-install
hardening applied.

## Part 4B fixes

- Proxmox LXC installs explicitly set `APP_ENV=production`.
- Installer monitoring timeout increased from 10 to 30 minutes so a slow
  first Docker build is not mistaken for a hung installation.
- `lxc-update.sh` now uses configured `WEB_PORT` and `API_PORT` values instead
  of assuming 3000/8080.
- `lxc-rollback.sh` now uses the same configured ports.
- Added `scripts/release-self-test.sh` for static release invariants.

## Verification

- Frontend: `tsc -p frontend/tsconfig.json --noEmit` → exit 0.
- Focused backend regression suite → exit 0.
- Installer/update/rollback/update-agent/storage/CLI shell files pass `bash -n`.
- `scripts/release-self-test.sh` → `Release static self-test: OK`.

The packaging environment cannot emulate nested Docker inside an actual
Proxmox unprivileged LXC. The installer therefore performs the final runtime
checks inside the newly-created LXC before writing `COMPLETE`.

## Publish

```powershell
git add .
git commit -m "release: Commit 002F stabilization RC"
git push origin main
```

## Clean install

```bash
bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?nocache=$(date +%s)")"
```
