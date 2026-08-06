# Mail Attachment Hub

Mail Attachment Hub securely collects email attachments and routes them to one or more storage services.

## Current delivery

**Sprint 0 · Step 010 — complete storage platform**

The application now includes:

- multiple encrypted IMAP accounts
- Gmail and Microsoft mail OAuth foundations
- scheduled attachment ingestion
- advanced attachment rules
- multiple destinations per rule
- local storage
- Google Drive
- OneDrive
- Dropbox
- S3 and MinIO
- Azure Blob Storage
- WebDAV and Nextcloud
- SFTP
- SMB/NAS
- encrypted storage configuration
- connection testing and health state
- upload retries and execution deduplication
- React management pages
- Docker Compose and GitHub Actions

## Start locally

```bash
make init
make check
make test
make up
make storage-platform-smoke
```

Open:

- UI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8080/docs`

## Configure storage

Open **Lagring** in the web interface. Create a destination, enter the provider fields and press **Testa**.

OAuth providers currently accept rclone-compatible token JSON. Generate it on a trusted computer:

```bash
rclone authorize drive
rclone authorize onedrive
rclone authorize dropbox
```

Paste the resulting token JSON into the provider's token field.

## Security

Provider credentials are encrypted with a key derived from `APP_SECRET_KEY`. Never commit `.env`, and do not change `APP_SECRET_KEY` after credentials are stored unless all credentials are re-entered.
