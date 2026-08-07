from datetime import UTC, datetime, timedelta

from mailhub.db.models import EmailAccount


def effective_sync_interval_seconds(
    account: EmailAccount,
    global_interval_seconds: int,
) -> int:
    value = account.sync_interval_seconds
    if value is None:
        value = global_interval_seconds
    return max(60, min(int(value), 86400))


def next_sync_at(
    account: EmailAccount,
    global_interval_seconds: int,
) -> datetime | None:
    if not account.is_enabled:
        return None

    if account.last_sync_at is None:
        return datetime.now(UTC)

    last_sync = account.last_sync_at
    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=UTC)

    return last_sync + timedelta(
        seconds=effective_sync_interval_seconds(
            account,
            global_interval_seconds,
        )
    )


def account_sync_due(
    account: EmailAccount,
    global_interval_seconds: int,
    *,
    now: datetime | None = None,
) -> bool:
    if not account.is_enabled:
        return False

    # A newly configured account has never completed a sync and should be
    # picked up immediately on the next worker cycle.
    if account.last_sync_at is None:
        return True

    due_at = next_sync_at(account, global_interval_seconds)
    if due_at is None:
        return False

    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)

    return due_at <= current
