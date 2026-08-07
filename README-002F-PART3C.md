# Commit 002F – Part 3C
## Installer completion + IP/port/login + CLI + recovery

Apply after Parts 3A and 3B.

### Reliable installation result

The installer now writes a verified result file inside the LXC:

```text
/root/mailhub-install-info.txt
```

It contains:

- hostname;
- IP address;
- Web UI URL;
- API URL;
- admin email;
- generated admin password;
- installed Git commit;
- useful operational commands.

The Proxmox-side installer reads this file after the background installation
has reached `COMPLETE`.

If the final display step has a transient `pct exec` problem, the already
completed application installation is no longer incorrectly reported as
failed.

### Final doctor check

Before writing:

```text
COMPLETE
```

the LXC installer runs:

```bash
mailhub doctor
```

Installation only completes if the final system diagnostics pass.

### New MailHub CLI

The installed command is now sourced from:

```text
scripts/mailhub-cli.sh
```

and installed as:

```text
/usr/local/bin/mailhub
```

Commands:

```text
mailhub credentials
mailhub status
mailhub doctor
mailhub logs [service]
mailhub restart [service]
mailhub update
mailhub update-status
mailhub repair storage
mailhub repair update-agent
mailhub help
```

### `mailhub doctor`

Checks:

1. Git repository / installed commit
2. Docker Compose
3. container state
4. backend health
5. frontend reachability
6. `/data/attachments` and `/data/routed`
7. update-agent + `status.json`

It exits non-zero if any required check fails, so it can also be used for
installation and maintenance verification.

### Updates

`scripts/lxc-update.sh` now refreshes `/usr/local/bin/mailhub` from the
repository after pulling new code.

After a successful update it also regenerates:

```text
/root/mailhub-install-info.txt
```

so installed commit/IP/port information remains current.

### Verification performed

All changed shell scripts passed:

```text
bash -n
```

A static regression test also passed:

```text
MailHub CLI/install-result regression checks: OK
```

### Apply

```powershell
git add proxmox/install.sh `
        scripts/lxc-update.sh `
        scripts/mailhub-cli.sh `
        scripts/write-install-info.sh `
        scripts/test-mailhub-cli.sh

git update-index --chmod=+x proxmox/install.sh
git update-index --chmod=+x scripts/lxc-update.sh
git update-index --chmod=+x scripts/mailhub-cli.sh
git update-index --chmod=+x scripts/write-install-info.sh
git update-index --chmod=+x scripts/test-mailhub-cli.sh

git commit -m "feat(lxc): add reliable install result and operations CLI"
git push origin main
```

### Existing LXC

After pulling the code:

```bash
pct enter 134
cd /opt/mail-attachment-hub
git pull --ff-only origin main

install -m 0755 scripts/mailhub-cli.sh /usr/local/bin/mailhub

chmod +x scripts/write-install-info.sh
scripts/write-install-info.sh

mailhub credentials
mailhub doctor
```

From the Proxmox host:

```bash
pct exec 134 -- mailhub credentials
pct exec 134 -- mailhub doctor
```
