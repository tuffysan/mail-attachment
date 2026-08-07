# Mail Attachment Hub – Commit 002F Final Release Candidate

This package contains the complete 002F stabilization release plus Part 4C
release verification.

## Part 4C additions

- `VERSION` file with release identifier `002F`.
- `mailhub version`.
- `mailhub verify`.
- `scripts/post-install-check.sh`.
- `release-manifest-002F.json` with SHA-256 hashes for critical release files.
- Proxmox installer runs both `mailhub doctor` and `mailhub verify` before
  writing `COMPLETE`.
- `/root/mailhub-install-info.txt` now includes the release version.

## Post-install verification

Inside the LXC:

```bash
mailhub version
mailhub credentials
mailhub verify
```

The full verification checks:

- clean Git working tree;
- Docker Compose configuration;
- postgres, redis, backend, worker and frontend running;
- backend live endpoint;
- backend readiness endpoint;
- frontend HTTP;
- storage read/write/traverse tests;
- update-agent systemd path;
- valid non-empty update-agent status JSON;
- saved installation information.

## Build-time verification

- Frontend TypeScript: exit code 0.
- Focused backend regression suite: exit code 0.
- Release static self-test: passed.
- Important shell scripts: `bash -n` passed.

A real nested Docker/LXC boot must still be executed on Proxmox. The installer
now performs the runtime verification there and refuses to report COMPLETE if
the required checks fail.

## Publish

```powershell
git add .
git commit -m "release: Commit 002F final candidate"
git push origin main
```

## Clean installation

```bash
bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?nocache=$(date +%s)")"
```
