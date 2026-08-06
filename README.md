# Mail Attachment Hub

Mail Attachment Hub securely collects email attachments and routes them according to user-defined rules.

## Current delivery

**Sprint 0 · Step 009 — complete attachment rule engine**

This snapshot includes:

- FastAPI, React, PostgreSQL, Redis and scheduled worker
- local admin login and JWT
- multiple encrypted IMAP accounts
- Gmail and Microsoft OAuth foundations
- incremental mailbox sync and attachment extraction
- duplicate protection and activity history
- rule priorities and stop-processing behavior
- filters for sender, recipient, subject, filename, content type and size
- multiple destinations per rule
- dynamic folder templates
- rule simulation in the web interface
- automatic routing to a persistent local destination

Remote storage providers are added in Step 010.

## Start locally

```bash
make init
make check
make test
make up
make rule-engine-smoke
```

Open:

- UI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8080/docs`

## Example rule

- Sender: `@supplier\.com$`
- Subject: `invoice|faktura`
- Filename: `\.pdf$`
- Folder: `Invoices/{year}/{month}/{sender}`
- Destination: `Local routed files`

Bilagor kopieras till Docker-volymen `routed_data`.
