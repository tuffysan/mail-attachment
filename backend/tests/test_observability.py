import json
import logging

from mailhub.core.observability.context import correlation_id_var, request_id_var
from mailhub.core.observability.logging import JsonFormatter


def test_json_formatter_contains_context_and_extra_fields() -> None:
    request_token = request_id_var.set("request-123")
    correlation_token = correlation_id_var.set("correlation-456")
    try:
        record = logging.LogRecord(
            name="mailhub.test", level=logging.INFO, pathname=__file__, lineno=12,
            msg="processed", args=(), exc_info=None,
        )
        record.duration_ms = 12.5
        rendered = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(request_token)
        correlation_id_var.reset(correlation_token)

    assert rendered["message"] == "processed"
    assert rendered["request_id"] == "request-123"
    assert rendered["correlation_id"] == "correlation-456"
    assert rendered["fields"]["duration_ms"] == 12.5


def test_json_formatter_ignores_non_serializable_extras() -> None:
    record = logging.LogRecord(
        name="mailhub.test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="safe", args=(), exc_info=None,
    )
    record.callback = lambda: None
    rendered = json.loads(JsonFormatter().format(record))
    assert "callback" not in rendered.get("fields", {})
