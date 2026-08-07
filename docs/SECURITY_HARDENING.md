# Security Hardening – Part 5E

Part 5E adds account/session hardening without changing the existing deployment
architecture.

## Session invalidation

Users now have a `token_version` column.

Every JWT includes the user's current token version. Protected endpoints reject
a token when its version no longer matches the database.

Changing the password increments `token_version`, invalidating all previously
issued access tokens immediately.

Migration:

```text
0010_security_hardening.py
```

## Login rate limiting

The authentication endpoint limits repeated login attempts by the combination
of remote address and email address.

Default behavior:

```text
10 attempts / 5 minutes
```

Successful login clears the bucket.

The limiter is intentionally local to the backend process. It provides useful
protection for the normal single-backend LXC deployment. A future horizontally
scaled deployment should move rate-limit state to Redis.

## Audit log

Login success, login failure and password changes are stored in the existing
`audit_logs` table.

Administrators can read recent entries through:

```text
GET /api/v1/auth/audit
```

## Password change

New endpoint:

```text
POST /api/v1/auth/password
```

The user must supply the current password and a new password of at least 12
characters.

After a successful change all older JWT sessions become invalid.

## Web UI

New page:

```text
/security
```

It provides:

- password change;
- explicit logout;
- current-user information;
- administrator security/audit history.

## Production defaults

The existing production Settings validation remains in force:

- placeholder `APP_SECRET_KEY` is rejected;
- placeholder admin password is rejected;
- OAuth client id/secret pairs must be complete.

Part 5E builds on these controls rather than weakening them.
