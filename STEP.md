# Sprint 0 · Step 007

## Goal

Add the first real email integration layer: multiple encrypted IMAP accounts, account management APIs, connection testing and a user-friendly web page.

## Included

- `email_accounts` database table and Alembic revision `0003`
- encrypted IMAP passwords using a key derived from `APP_SECRET_KEY`
- authenticated CRUD API for multiple email accounts
- safe IMAP connection and mailbox test
- support for SSL/TLS and selectable mailbox
- React page for adding, listing, testing and deleting accounts
- Gmail-friendly defaults (`imap.gmail.com`, port 993, SSL)
- backend unit tests and end-to-end CRUD smoke test
- CI coverage for the new API and frontend files

## Not included yet

- Gmail OAuth/XOAUTH2
- scheduled mailbox polling
- attachment download
- attachment rules
- storage destinations
- Proxmox production installer

## Acceptance criteria

```bash
make init
make check
make test
make up
make api-smoke
make migration-smoke
make auth-smoke
make frontend-smoke
make email-account-smoke
```

Open `http://127.0.0.1:3000`, sign in and create an IMAP account from **E-postkonton**.
