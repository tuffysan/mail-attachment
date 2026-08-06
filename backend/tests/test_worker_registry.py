from mailhub.core.lifecycle.workers import WorkerRegistry, WorkerState


def test_worker_registry_tracks_lifecycle() -> None:
    registry = WorkerRegistry()
    worker = registry.register("mail-sync")
    assert worker.state == WorkerState.STARTING

    registry.set_state("mail-sync", WorkerState.RUNNING)
    registry.heartbeat("mail-sync", activity=True)
    registry.record_cycle("mail-sync")
    snapshot = registry.get("mail-sync")

    assert snapshot is not None
    assert snapshot.state == WorkerState.RUNNING
    assert snapshot.processed_cycles == 1
    assert snapshot.last_activity_at is not None


def test_worker_failure_does_not_expose_message() -> None:
    registry = WorkerRegistry()
    registry.register("mail-sync")
    registry.record_failure("mail-sync", RuntimeError("database password"))

    snapshot = registry.get("mail-sync")
    assert snapshot is not None
    assert snapshot.state == WorkerState.FAILED
    assert snapshot.failures == 1
    assert snapshot.last_error == "RuntimeError"
    assert "database password" not in snapshot.last_error
