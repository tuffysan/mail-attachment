from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from mailhub.mail.schedule import (
    account_sync_due,
    effective_sync_interval_seconds,
    next_sync_at,
)


def account(**values):
    defaults = {
        "is_enabled": True,
        "sync_interval_seconds": None,
        "last_sync_at": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_effective_interval_uses_global_fallback() -> None:
    assert effective_sync_interval_seconds(account(), 300) == 300


def test_effective_interval_uses_account_override() -> None:
    assert effective_sync_interval_seconds(
        account(sync_interval_seconds=900),
        300,
    ) == 900


def test_disabled_account_is_never_due() -> None:
    assert not account_sync_due(
        account(is_enabled=False),
        300,
        now=datetime.now(UTC),
    )


def test_never_synced_account_is_due() -> None:
    assert account_sync_due(
        account(last_sync_at=None),
        300,
        now=datetime.now(UTC),
    )


def test_recent_account_waits_for_own_interval() -> None:
    now = datetime(2026, 8, 7, 20, 0, tzinfo=UTC)
    item = account(
        sync_interval_seconds=900,
        last_sync_at=now - timedelta(minutes=5),
    )

    assert not account_sync_due(item, 300, now=now)
    assert next_sync_at(item, 300) == now + timedelta(minutes=10)


def test_due_after_interval() -> None:
    now = datetime(2026, 8, 7, 20, 0, tzinfo=UTC)
    item = account(
        sync_interval_seconds=300,
        last_sync_at=now - timedelta(minutes=6),
    )

    assert account_sync_due(item, 600, now=now)
