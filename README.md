# Mail Attachment Hub v1.0.0

Open-source email attachment automation with multiple email accounts, advanced rules and multiple storage destinations.

## Features

- Gmail, Microsoft 365 and standard IMAP
- multiple email accounts
- scheduled and manual mailbox synchronization
- secure attachment extraction and ZIP limits
- advanced rule engine with simulation
- multiple storage destinations per rule
- Google Drive, OneDrive, Dropbox, S3, MinIO, Azure Blob, WebDAV, Nextcloud, SFTP, SMB and local storage
- encrypted credentials and tokens
- React web interface and FastAPI
- PostgreSQL, Redis, Docker Compose
- audit logs, administration statistics and API-key foundation
- backup, restore, diagnostics and upgrades
- Docker and Proxmox installation

## Docker one-line installation

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/install.sh)"
```

## Proxmox LXC one-line installation

Run as root on a Proxmox host:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/tuffysan/mail-attachment/main/installer/proxmox/install.sh)"
```

## Development

```bash
make init
make check
make test
make up
```

Web UI: `http://127.0.0.1:3000`

## Production HTTPS

Set `DOMAIN` and `LETSENCRYPT_EMAIL` in `.env`, then:

```bash
make production-up
```

## Operations

```bash
make doctor
make backup
./scripts/restore.sh backups/<backup-directory>
./scripts/update.sh
```

## Important

A full clean-install and provider-by-provider end-to-end test must be run in your own Docker/Proxmox environment before exposing the application publicly.
