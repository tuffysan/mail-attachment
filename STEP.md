# Sprint 0 · Step 008

## Goal
Deliver the complete email ingestion engine as one coherent increment.

## Included
- password IMAP and XOAUTH2 authentication
- Google Gmail and Microsoft 365 OAuth authorization-code flows
- encrypted refresh/access tokens
- scheduled worker with retry attempts
- manual sync endpoint
- UID-based incremental mailbox scanning
- MIME parsing and safe attachment extraction
- optional bounded ZIP extraction
- local attachment staging volume
- message, attachment, sync-run and activity-event tables
- per-message and per-attachment duplicate protection
- message/activity APIs and worker smoke tests
- UI buttons for OAuth and manual synchronization

## Operational notes
OAuth requires application credentials in `.env` and exact callback URLs registered with Google or Microsoft.
Extracted attachments remain in the Docker `attachment_data` volume until routing/storage is added in Step 010.

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
```
