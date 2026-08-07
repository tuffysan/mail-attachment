from mailhub.auth.rate_limit import (
    check_login_rate_limit,
    clear_login_rate_limit,
    reset_rate_limits,
)

def setup_function() -> None:
    reset_rate_limits()

def test_login_rate_limit_blocks_after_limit() -> None:
    key = "127.0.0.1:user@example.com"
    for _ in range(3):
        allowed, retry_after = check_login_rate_limit(
            key, limit=3, window_seconds=60
        )
        assert allowed
        assert retry_after == 0

    allowed, retry_after = check_login_rate_limit(
        key, limit=3, window_seconds=60
    )
    assert not allowed
    assert retry_after >= 1

def test_clear_login_rate_limit_resets_bucket() -> None:
    key = "127.0.0.1:user@example.com"
    check_login_rate_limit(key, limit=1, window_seconds=60)
    clear_login_rate_limit(key)
    allowed, _ = check_login_rate_limit(key, limit=1, window_seconds=60)
    assert allowed
