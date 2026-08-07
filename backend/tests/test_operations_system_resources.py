from mailhub.operations.system_resources import collect_system_resources


def test_collect_system_resources_returns_sane_values() -> None:
    resources = collect_system_resources("/")

    assert resources.cpu_count >= 1
    assert resources.memory_total_bytes >= 0
    assert resources.memory_available_bytes >= 0
    assert 0 <= resources.memory_used_percent <= 100
    assert resources.disk_total_bytes > 0
    assert resources.disk_free_bytes >= 0
    assert 0 <= resources.disk_used_percent <= 100
    assert resources.uptime_seconds is None or resources.uptime_seconds >= 0
