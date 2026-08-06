# Sprint 0 · Step 010

## Goal

Deliver one storage platform that supports local and remote destinations through a common encrypted configuration and upload interface.

## Included

- local filesystem
- Google Drive
- Microsoft OneDrive
- Dropbox
- Amazon S3 and S3-compatible services
- MinIO
- Azure Blob Storage
- WebDAV and Nextcloud
- SFTP
- SMB/NAS
- rclone installed in backend and worker images
- encrypted provider configuration
- multiple accounts for every provider
- connection testing and stored health state
- provider-aware upload with retries
- existing per-rule/per-attachment/per-destination deduplication
- storage management API and React page
- migration `0006`
- unit and CI smoke tests

## Authentication notes

OAuth-capable rclone providers accept an rclone-compatible `token` JSON value.
Tokens can be generated using `rclone authorize <provider>` on a trusted computer.
A later production wizard may automate more of this flow.

## Acceptance criteria

```bash
make init
make check
make test
make up
make migration-smoke
make auth-smoke
make frontend-smoke
make email-account-smoke
make mail-engine-smoke
make rule-engine-smoke
make storage-platform-smoke
```
