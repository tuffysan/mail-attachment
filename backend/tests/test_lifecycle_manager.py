import asyncio

import pytest

from mailhub.core.lifecycle.manager import LifecycleManager


@pytest.mark.asyncio
async def test_hooks_run_in_dependency_order() -> None:
    events: list[str] = []
    manager = LifecycleManager()

    async def startup_one() -> None:
        events.append("start-one")

    async def startup_two() -> None:
        events.append("start-two")

    async def shutdown_one() -> None:
        events.append("stop-one")

    async def shutdown_two() -> None:
        events.append("stop-two")

    manager.add_startup_hook("one", startup_one)
    manager.add_startup_hook("two", startup_two)
    manager.add_shutdown_hook("one", shutdown_one)
    manager.add_shutdown_hook("two", shutdown_two)

    await manager.run_startup_hooks()
    await manager.run_shutdown_hooks()

    assert events == ["start-one", "start-two", "stop-two", "stop-one"]


@pytest.mark.asyncio
async def test_shutdown_event_wakes_waiters() -> None:
    manager = LifecycleManager()
    waiter = asyncio.create_task(manager.wait_for_shutdown())
    await asyncio.sleep(0)
    manager.request_shutdown()
    await asyncio.wait_for(waiter, timeout=1)
    assert manager.shutdown_requested is True


@pytest.mark.asyncio
async def test_slow_shutdown_hook_is_bounded() -> None:
    manager = LifecycleManager(shutdown_timeout_seconds=0.01)

    async def slow() -> None:
        await asyncio.sleep(1)

    manager.add_shutdown_hook("slow", slow)
    await asyncio.wait_for(manager.run_shutdown_hooks(), timeout=0.5)
