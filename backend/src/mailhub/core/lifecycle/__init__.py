"""Application lifecycle and cooperative shutdown management."""

from mailhub.core.lifecycle.manager import LifecycleManager, lifecycle_manager
from mailhub.core.lifecycle.workers import (
    WorkerSnapshot,
    WorkerState,
    worker_registry,
)

__all__ = [
    "LifecycleManager",
    "WorkerSnapshot",
    "WorkerState",
    "lifecycle_manager",
    "worker_registry",
]
