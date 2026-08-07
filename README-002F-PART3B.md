# Commit 002F – Part 3B
## LXC storage permissions + Docker storage self-test

Apply after Part 3A.

This part addresses the earlier runtime failure:

```text
[Errno 13] Permission denied: '/data/routed/.mailhub-write-test'
```

### Storage init

`compose.override.lxc.yml` now runs a dedicated `storage-init` service as root
before backend/worker startup.

It:

- creates `/data/attachments` and `/data/routed`;
- recursively assigns UID/GID `10001:10001`;
- applies `0770` to directories;
- applies `0660` to existing files;
- verifies ownership;
- creates/removes probe files before reporting success.

Backend and worker depend on the successful completion of this init service.

### Installer verification

The Proxmox installer now explicitly runs:

```text
docker compose ... run --rm --no-deps storage-init
```

before starting the application stack.

After containers are running, it executes:

```text
scripts/storage-self-test.sh
```

The installation cannot complete unless both backend and worker can:

- read;
- write;
- traverse;
- create a non-empty file;
- read it back;
- remove it

in both:

```text
/data/attachments
/data/routed
```

### Updates

`scripts/lxc-update.sh` now reruns storage initialization before restarting the
updated stack and runs the same storage self-test after backend/frontend health
checks.

This prevents an update from silently reintroducing storage permission
problems.

### Repair existing LXC

New command:

```bash
cd /opt/mail-attachment-hub
chmod +x scripts/repair-storage-permissions.sh
./scripts/repair-storage-permissions.sh
```

It:

1. runs storage-init;
2. recreates backend and worker;
3. runs the full storage self-test.

### Verification performed

All modified shell scripts pass `bash -n`.

A static regression script also verifies the required storage mounts,
UID/GID, storage-init dependency and installer/update hooks:

```text
LXC storage configuration regression checks: OK
```

The final read/write verification is intentionally performed inside the real
backend and worker containers during installation/update because Docker volume
ownership inside your nested Proxmox LXC cannot be reproduced by the packaging
environment.

### Apply

```powershell
git add compose.override.lxc.yml `
        proxmox/install.sh `
        scripts/lxc-update.sh `
        scripts/storage-self-test.sh `
        scripts/repair-storage-permissions.sh `
        scripts/test-lxc-storage-config.sh

git update-index --chmod=+x proxmox/install.sh
git update-index --chmod=+x scripts/lxc-update.sh
git update-index --chmod=+x scripts/storage-self-test.sh
git update-index --chmod=+x scripts/repair-storage-permissions.sh
git update-index --chmod=+x scripts/test-lxc-storage-config.sh

git commit -m "fix(lxc): enforce storage ownership and container write tests"
git push origin main
```

### Existing LXC

After pulling the commit:

```bash
pct enter 134

cd /opt/mail-attachment-hub
git pull --ff-only origin main

chmod +x \
  scripts/storage-self-test.sh \
  scripts/repair-storage-permissions.sh

./scripts/repair-storage-permissions.sh
```

Expected final result:

```text
Backend:
READ_OK WRITE_OK TRAVERSE_OK

Worker:
READ_OK WRITE_OK TRAVERSE_OK

Storage self test: OK
```
