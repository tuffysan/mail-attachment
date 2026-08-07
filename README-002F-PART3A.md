# Commit 002F – Part 3A
## LXC installer + Update Agent + status.json integration

Apply after backend Parts 1A–1E and frontend Parts 2A–2D.

### Fixed installation contract

The Proxmox installer now treats GitHub Update as a required, verified LXC
feature rather than an optional post-install step.

Installation order:

```text
clone repository
→ require update-agent scripts
→ chmod scripts
→ install update-agent
→ verify systemd path unit
→ verify /var/lib/mailhub-control ownership/write access
→ create .env
→ build/start Docker
→ verify backend /control mount
→ submit a real GitHub "check" request
→ wait for systemd update-agent
→ validate non-empty status.json
→ verify backend sees the same valid status
→ continue normal API/frontend health checks
→ report installation complete
```

The installer cannot report COMPLETE if the end-to-end update-agent check fails.

### status.json safety

`install-update-agent.sh` repairs `status.json` whenever it is:

- missing;
- zero bytes;
- invalid JSON.

The replacement file is generated with `jq`, validated, permissioned and moved
atomically.

`update-agent.sh` also:

- validates `request.json` before processing it;
- writes an emergency valid JSON status if the agent exits unexpectedly;
- never intentionally replaces the live status with an empty temporary file.

### Repair command for an existing LXC

New file:

```text
scripts/repair-update-agent.sh
```

Run:

```bash
cd /opt/mail-attachment-hub
chmod +x scripts/repair-update-agent.sh
./scripts/repair-update-agent.sh
```

It verifies:

- systemd agent enabled/active;
- control directory owner/mode;
- valid non-empty status JSON;
- backend READ/WRITE access to `/control`;
- real end-to-end GitHub check.

### Verification performed

Shell syntax:

```text
proxmox/install.sh                    OK
scripts/install-update-agent.sh       OK
scripts/update-agent.sh               OK
scripts/lxc-update.sh                 OK
scripts/repair-update-agent.sh        OK
```

All passed `bash -n`.

A local regression test also sent an intentionally invalid request JSON to
`update-agent.sh`. It exited with an error but produced a non-empty, valid
`status.json` with state `error`, proving the zero-byte failure path is guarded.

A complete Proxmox/LXC boot cannot be emulated in the packaging environment;
the new installer performs that final end-to-end validation on the real LXC and
aborts installation if it fails.

### Apply

```powershell
git add proxmox/install.sh `
        scripts/install-update-agent.sh `
        scripts/update-agent.sh `
        scripts/lxc-update.sh `
        scripts/repair-update-agent.sh

git update-index --chmod=+x proxmox/install.sh
git update-index --chmod=+x scripts/install-update-agent.sh
git update-index --chmod=+x scripts/update-agent.sh
git update-index --chmod=+x scripts/lxc-update.sh
git update-index --chmod=+x scripts/repair-update-agent.sh

git commit -m "fix(lxc): verify update agent end to end during install"
git push origin main
```

### Clean installation

After pushing to GitHub:

```bash
pct stop 134 2>/dev/null || true
pct destroy 134 --purge 2>/dev/null || true

bash -c "$(curl -fsSL "https://raw.githubusercontent.com/tuffysan/mail-attachment/main/proxmox/install.sh?nocache=$(date +%s)")"
```

During installation you should see:

```text
Installing MailHub Update Agent
Update agent control directory: writable
Självtestar GitHub update-agent
Update agent end-to-end: OK
```
