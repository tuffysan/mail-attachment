# Local storage permissions

Mail Attachment Hub backend and worker containers run as the unprivileged
`mailhub` account with UID/GID `10001`.

Docker named volumes are initially created as root. The `storage-init` service
repairs ownership before backend startup:

```text
/data/attachments -> 10001:10001
/data/routed      -> 10001:10001
```

The default directory mode is `0770`.

## Web administration

For a local storage destination, open **Storage / Lagring** and select
**Rättigheter**.

Administrators can inspect:

- path;
- owner UID;
- group GID;
- Unix mode;
- whether the backend process can write to the directory.

Administrators can change the Unix mode and optionally apply it recursively.

Ownership is intentionally not changeable from the web application. The backend
continues to run without root privileges.

## Existing LXC

After updating the code:

```bash
cd /opt/mail-attachment-hub
chmod +x scripts/fix-storage-permissions.sh
./scripts/fix-storage-permissions.sh
```

Then test **Local routed files** again from the web UI.
