# Commit 002F — Part 1A: Database / ORM stabilization

This overlay fixes the PostgreSQL error:

`null value in column "created_at" of relation "email_accounts" violates not-null constraint`

## Root cause

`TimestampMixin` uses `server_default=func.now()`, so SQLAlchemy omits timestamp
columns on INSERT and expects PostgreSQL to fill them. Several Alembic migrations
created `created_at` / `updated_at` as `NOT NULL` **without a database default**.

## Fix

- Adds migration `0008_timestamp_defaults.py` for existing databases.
- Adds `DEFAULT now()` to historical migrations for clean installations.
- Repairs all affected TimestampMixin tables, not only `email_accounts`.
- Adds a regression test for ORM timestamp defaults.

## Apply

Copy the files over the repository root and commit:

```powershell
git add backend/alembic/versions backend/tests/test_timestamp_defaults.py
git commit -m "fix(db): align timestamp defaults with ORM"
git push origin main
```

Then update/rebuild the LXC. On backend startup Alembic should show:

```text
Running upgrade 0007 -> 0008, Align timestamp defaults with TimestampMixin.
```

After that, creating an IMAP account should no longer fail because of
`email_accounts.created_at` / `updated_at`.
