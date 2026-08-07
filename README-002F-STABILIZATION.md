# Mail Attachment Hub – Commit 002F Stabilization

This package integrates Parts 1A–1E, 2A–2D and 3A–3D over the uploaded project.

## Included

- Database timestamp/default migration and ORM alignment
- Backend settings/model stabilization
- IMAP password and OAuth/XOAUTH2 credential handling
- Google OAuth validation and callback hardening
- Backend regression/self-test additions
- Email Accounts frontend validation before save
- Setup Wizard and Dashboard improvements
- Rules simulation and Storage UX improvements
- Operations/GitHub Update frontend hardening
- LXC update-agent installation and end-to-end verification
- Atomic/non-empty update `status.json`
- Storage ownership/write tests for backend and worker
- Reliable IP/port/login installation output
- `mailhub` CLI and `mailhub doctor`
- Update rollback support

## Verification performed in packaging environment

Frontend TypeScript:

```text
tsc -p frontend/tsconfig.json --noEmit
exit code: 0
```

Backend focused suite:

```text
exit code: 0
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                            [100%][0m
```

Shell syntax checks were run with `bash -n` for the installer, update-agent,
storage, CLI and rollback scripts.

A real nested Docker-in-LXC installation cannot be emulated here. The Proxmox
installer itself now performs the final runtime checks in the actual LXC and
will not report COMPLETE unless its required self-tests pass.

## Recommended commit

```powershell
git add .
git commit -m "release: Commit 002F stabilization"
git push origin main
```

## Fresh Proxmox installation

```bash
bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?nocache=$(date +%s)")"
```
