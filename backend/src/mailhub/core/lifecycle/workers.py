import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum


class WorkerState(StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class WorkerSnapshot:
    name: str
    state: WorkerState
    started_at: datetime | None
    heartbeat_at: datetime | None
    last_activity_at: datetime | None
    processed_cycles: int
    failures: int
    last_error: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class WorkerRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workers: dict[str, WorkerSnapshot] = {}

    def register(self, name: str) -> WorkerSnapshot:
        now = datetime.now(UTC)
        snapshot = WorkerSnapshot(
            name=name,
            state=WorkerState.STARTING,
            started_at=now,
            heartbeat_at=now,
            last_activity_at=None,
            processed_cycles=0,
            failures=0,
            last_error=None,
        )
        with self._lock:
            self._workers[name] = snapshot
        return snapshot

    def set_state(self, name: str, state: WorkerState) -> None:
        with self._lock:
            worker = self._workers[name]
            worker.state = state
            worker.heartbeat_at = datetime.now(UTC)

    def heartbeat(self, name: str, *, activity: bool = False) -> None:
        now = datetime.now(UTC)
        with self._lock:
            worker = self._workers[name]
            worker.heartbeat_at = now
            if activity:
                worker.last_activity_at = now

    def record_cycle(self, name: str) -> None:
        with self._lock:
            worker = self._workers[name]
            worker.processed_cycles += 1
            worker.last_activity_at = datetime.now(UTC)
            worker.heartbeat_at = worker.last_activity_at
            worker.last_error = None

    def record_failure(self, name: str, error: Exception) -> None:
        with self._lock:
            worker = self._workers[name]
            worker.failures += 1
            worker.last_error = type(error).__name__
            worker.state = WorkerState.FAILED
            worker.heartbeat_at = datetime.now(UTC)

    def get(self, name: str) -> WorkerSnapshot | None:
        with self._lock:
            worker = self._workers.get(name)
            return None if worker is None else WorkerSnapshot(**asdict(worker))

    def snapshots(self) -> list[WorkerSnapshot]:
        with self._lock:
            return [WorkerSnapshot(**asdict(worker)) for worker in self._workers.values()]

    def reset(self) -> None:
        with self._lock:
            self._workers.clear()


worker_registry = WorkerRegistry()
