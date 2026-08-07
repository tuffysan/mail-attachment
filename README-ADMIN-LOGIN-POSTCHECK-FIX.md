# Admin Login + Post Install Fix

This patch fixes two related installation problems.

## 1. Admin credentials are always shown

The installer now prints the generated credentials immediately after they are
created and again before the final doctor/post-install checks.

If a later post-install check fails, the Proxmox-side installer explicitly reads
`/root/mailhub-credentials.env` and prints the credentials before returning the
installation error.

So even a partially failed final verification will show:

```text
============================================================
 ADMIN LOGIN
============================================================
Web UI:         http://<LXC-IP>:3000
API:            http://<LXC-IP>:8080
Admin email:    admin@example.com
Admin password: <generated password>
============================================================
```

## 2. False "Git working tree contains local changes" fixed

The installer intentionally runs `chmod +x` on tracked shell scripts. Git can
interpret these executable-bit changes as local modifications.

The deployment checkout now uses:

```bash
git config core.fileMode false
```

before installer-managed chmod operations.

`post-install-check.sh` applies the same setting before checking repository
cleanliness and prints `git status --short` if genuine content changes remain.

This also prevents installer-created file-mode changes from later blocking the
GitHub update agent with:

```text
Local changes detected. Update aborted.
```

## Apply

```powershell
git add proxmox/install.sh scripts/post-install-check.sh
git update-index --chmod=+x proxmox/install.sh
git update-index --chmod=+x scripts/post-install-check.sh
git commit -m "fix(installer): always show credentials and ignore managed file modes"
git push origin main
```
