# Local storage ownership repair

The backend image runs as:

```text
UID 10001
GID 10001
```

Docker named volumes are created independently and can initially be owned by
root. The LXC compose override therefore includes a one-shot `storage-init`
service.

Before backend and worker startup it applies:

```text
/data/attachments -> 10001:10001, mode 0770
/data/routed      -> 10001:10001, mode 0770
```

## Existing LXC

Run:

```bash
cd /opt/mail-attachment-hub
chmod +x scripts/fix-storage-permissions.sh
./scripts/fix-storage-permissions.sh
```

Expected result:

```text
/data/routed: uid=10001 gid=10001 mode=0o770 writable=True
  write test: OK
/data/attachments: uid=10001 gid=10001 mode=0o770 writable=True
  write test: OK
```

Then use **Lagring → Local routed files → Testa** again.

## Check later

```bash
./scripts/storage-permissions-status.sh
```
