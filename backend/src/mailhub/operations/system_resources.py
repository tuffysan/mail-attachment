import os
import shutil
from pathlib import Path

from mailhub.operations.schemas import OperationsSystemResources


def _memory_bytes() -> tuple[int, int]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            first = raw.strip().split()[0]
            values[key] = int(first) * 1024
    except (OSError, ValueError, IndexError):
        return 0, 0

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    return total, available


def _uptime_seconds() -> float | None:
    try:
        return float(
            Path("/proc/uptime")
            .read_text(encoding="utf-8")
            .split()[0]
        )
    except (OSError, ValueError, IndexError):
        return None


def collect_system_resources(
    disk_path: str = "/data/routed",
) -> OperationsSystemResources:
    try:
        load_1m, load_5m, load_15m = os.getloadavg()
    except (AttributeError, OSError):
        load_1m = load_5m = load_15m = None

    memory_total, memory_available = _memory_bytes()
    memory_used = max(0, memory_total - memory_available)
    memory_percent = (
        round((memory_used / memory_total) * 100, 1)
        if memory_total > 0
        else 0.0
    )

    try:
        usage = shutil.disk_usage(disk_path)
    except OSError:
        usage = shutil.disk_usage("/")

    disk_used = max(0, usage.total - usage.free)
    disk_percent = (
        round((disk_used / usage.total) * 100, 1)
        if usage.total > 0
        else 0.0
    )

    return OperationsSystemResources(
        cpu_count=os.cpu_count() or 1,
        load_1m=round(load_1m, 2) if load_1m is not None else None,
        load_5m=round(load_5m, 2) if load_5m is not None else None,
        load_15m=round(load_15m, 2) if load_15m is not None else None,
        memory_total_bytes=memory_total,
        memory_available_bytes=memory_available,
        memory_used_percent=memory_percent,
        disk_total_bytes=usage.total,
        disk_free_bytes=usage.free,
        disk_used_percent=disk_percent,
        uptime_seconds=_uptime_seconds(),
    )
