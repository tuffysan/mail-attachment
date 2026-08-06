from mailhub.core.health.state import StartupState


def test_startup_state_lifecycle() -> None:
    state = StartupState()
    state.begin()
    assert state.started_at is not None
    assert state.startup_complete is False

    state.mark_ready()
    assert state.startup_complete is True
    assert state.ready_at is not None
    assert state.startup_error is None

    state.mark_shutdown()
    assert state.shutting_down is True


def test_startup_state_records_safe_error_type() -> None:
    state = StartupState()
    state.begin()
    state.mark_failed(RuntimeError("secret details"))

    assert state.startup_complete is False
    assert state.startup_error == "RuntimeError"
    assert "secret details" not in state.startup_error
