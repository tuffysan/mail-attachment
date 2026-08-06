from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class StartupState:
    started_at: datetime | None = None
    ready_at: datetime | None = None
    shutdown_started_at: datetime | None = None
    shutting_down: bool = False
    startup_complete: bool = False
    startup_error: str | None = None

    def begin(self) -> None:
        self.started_at = datetime.now(UTC)
        self.ready_at = None
        self.shutdown_started_at = None
        self.shutting_down = False
        self.startup_complete = False
        self.startup_error = None

    def mark_ready(self) -> None:
        self.ready_at = datetime.now(UTC)
        self.startup_complete = True
        self.startup_error = None

    def mark_failed(self, error: Exception) -> None:
        self.startup_complete = False
        self.startup_error = type(error).__name__

    def mark_shutdown(self) -> None:
        self.shutting_down = True
        self.shutdown_started_at = datetime.now(UTC)


startup_state = StartupState()
