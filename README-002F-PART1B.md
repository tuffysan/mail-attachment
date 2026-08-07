# Commit 002F – Part 1B Backend Stabilization

This overlay follows Part 1A.

## Fixes

### SystemMetadata ORM / migration alignment

Migration `0001` already creates:

- `uq_system_metadata_key` as a named unique constraint;
- `ix_system_metadata_key` as a separate non-unique index.

The ORM used `unique=True, index=True`, which SQLAlchemy represented as one
unique index instead of the same constraint + index pair.

`SystemMetadata` now declares the named `UniqueConstraint` explicitly and keeps
the separate index, matching Alembic exactly.

### Safe development/test APP_SECRET_KEY default

Several existing tests and development utilities construct `Settings` without
supplying `APP_SECRET_KEY`. A development-only default is now available:

```text
development-secret-key-not-for-production
```

Production safety is preserved. The existing production validator rejects this
value because it contains `development-secret`.

Two regression tests verify:

1. test/development can use the safe local default;
2. production rejects the default.

## Apply

Copy this overlay over the repository after Part 1A.

```powershell
git add backend/src/mailhub/db/models.py `
        backend/src/mailhub/core/config/settings.py `
        backend/tests/test_settings.py

git commit -m "fix(backend): align metadata constraints and test settings"
git push origin main
```

## Verification

The following focused tests pass in the build workspace:

```text
tests/test_models.py
tests/test_config.py
tests/test_settings.py
```

`tests/test_database.py` advances past Settings validation but the local test
runner used to build this ZIP does not have the declared `asyncpg` dependency
installed. In the project container, `pip install .` installs `asyncpg` from
`pyproject.toml`, so this is an environment limitation rather than a code
failure.
