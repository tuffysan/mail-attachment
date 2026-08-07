# Fix for zero-byte status.json

Your diagnostics show:

```text
/control is readable: READ_OK
/control is writable: WRITE_OK
status.json size: 0 bytes
```

This means the problem is not permissions. The update agent wrote an empty
status file.

The fixed `update-agent.sh` always emits valid JSON and converts empty optional
fields to JSON `null`. It also refuses to replace `status.json` if the generated
temporary file is empty or invalid.

## Apply

Copy:

```text
scripts/update-agent.sh
scripts/repair-update-status.sh
```

to the repository.

Commit:

```powershell
git add scripts/update-agent.sh scripts/repair-update-status.sh
git update-index --chmod=+x scripts/update-agent.sh
git update-index --chmod=+x scripts/repair-update-status.sh
git commit -m "fix(update): prevent zero-byte status json"
git push origin main
```

## Repair existing LXC

```bash
pct enter 134

cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x scripts/repair-update-status.sh
./scripts/repair-update-status.sh
```

The result should show a non-empty `status.json` and state either:

```text
up_to_date
```

or:

```text
update_available
```
