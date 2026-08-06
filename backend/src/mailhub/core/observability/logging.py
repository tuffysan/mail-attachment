import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, Literal

from mailhub.core.observability.context import get_correlation_id, get_request_id

_STANDARD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class ContextFilter(logging.Filter):
    """Attach request context to records without coupling callers to HTTP code."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.correlation_id = get_correlation_id()
        return True


class JsonFormatter(logging.Formatter):
    """JSON formatter suitable for Docker, Loki and cloud log collectors."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None) or get_request_id()
        correlation_id = getattr(record, "correlation_id", None) or get_correlation_id()
        if request_id:
            payload["request_id"] = request_id
        if correlation_id:
            payload["correlation_id"] = correlation_id

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_FIELDS
            and key not in {"request_id", "correlation_id"}
            and not key.startswith("_")
            and _is_json_safe(value)
        }
        if extras:
            payload["fields"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        context = []
        if getattr(record, "request_id", None):
            context.append(f"request_id={record.request_id}")
        if getattr(record, "correlation_id", None):
            context.append(f"correlation_id={record.correlation_id}")
        suffix = f" [{' '.join(context)}]" if context else ""
        rendered = f"{datetime.now(UTC).isoformat()} {record.levelname:<8} {record.name}: {record.getMessage()}{suffix}"
        if record.exc_info:
            rendered += "\n" + self.formatException(record.exc_info)
        return rendered


def _is_json_safe(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return True


def configure_logging(level: str, log_format: Literal["json", "console"] = "json") -> None:
    """Configure a single root handler and normalize Uvicorn log propagation."""

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextFilter())
    handler.setFormatter(JsonFormatter() if log_format == "json" else ConsoleFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

    logging.captureWarnings(True)
