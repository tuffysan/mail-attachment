# Sprint 0 · Step 009

## Goal

Deliver a complete attachment rule engine with priorities, simulation, multiple destinations and automatic local routing.

## Included

- storage-destination model and CRUD API
- default local destination mounted at `/data/routed`
- rules scoped globally or to one email account
- regular-expression filters for sender, recipient, subject, filename and content type
- optional minimum and maximum attachment size
- rule priority and stop-processing behavior
- multiple destinations per rule
- safe dynamic folder templates
- supported variables: `year`, `month`, `day`, `sender`, `sender_email`, `subject`, `filename`, `extension`
- rule simulation API with match explanations
- automatic local copy after attachment ingestion
- per-rule/per-attachment/per-destination execution deduplication
- React rule builder and simulation interface
- migration `0005`, unit tests and CI smoke tests

## Not included yet

- Google Drive, OneDrive, Dropbox, S3, WebDAV, SFTP and SMB providers
- remote-provider retry queue
- production installer and upgrade UI

These arrive in Steps 010–012.

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
```
