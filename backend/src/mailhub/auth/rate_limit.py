import time
from collections import defaultdict, deque
from threading import Lock

_LOCK = Lock()
_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)

def check_login_rate_limit(
    key: str,
    *,
    limit: int = 10,
    window_seconds: int = 300,
) -> tuple[bool, int]:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _LOCK:
        attempts = _ATTEMPTS[key]
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if len(attempts) >= limit:
            retry_after = max(1, int(window_seconds - (now - attempts[0])))
            return False, retry_after
        attempts.append(now)
    return True, 0

def clear_login_rate_limit(key: str) -> None:
    with _LOCK:
        _ATTEMPTS.pop(key, None)

def reset_rate_limits() -> None:
    with _LOCK:
        _ATTEMPTS.clear()
