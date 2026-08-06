import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
AsyncHook = Callable[[], Awaitable[None]]


@dataclass
class LifecycleManager:
    shutdown_timeout_seconds: float = 30.0
    _shutdown_event: asyncio.Event = field(default_factory=asyncio.Event)
    _startup_hooks: list[tuple[str, AsyncHook]] = field(default_factory=list)
    _shutdown_hooks: list[tuple[str, AsyncHook]] = field(default_factory=list)

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_event.is_set()

    def request_shutdown(self) -> None:
        self._shutdown_event.set()

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def add_startup_hook(self, name: str, hook: AsyncHook) -> None:
        self._startup_hooks.append((name, hook))

    def add_shutdown_hook(self, name: str, hook: AsyncHook) -> None:
        self._shutdown_hooks.append((name, hook))

    async def run_startup_hooks(self) -> None:
        for name, hook in self._startup_hooks:
            logger.info("startup_hook_started", extra={"hook_name": name})
            await hook()
            logger.info("startup_hook_completed", extra={"hook_name": name})

    async def run_shutdown_hooks(self) -> None:
        for name, hook in reversed(self._shutdown_hooks):
            logger.info("shutdown_hook_started", extra={"hook_name": name})
            try:
                async with asyncio.timeout(self.shutdown_timeout_seconds):
                    await hook()
            except TimeoutError:
                logger.error("shutdown_hook_timed_out", extra={"hook_name": name})
            except Exception:
                logger.exception("shutdown_hook_failed", extra={"hook_name": name})
            else:
                logger.info("shutdown_hook_completed", extra={"hook_name": name})

    def reset(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._startup_hooks.clear()
        self._shutdown_hooks.clear()


lifecycle_manager = LifecycleManager()
