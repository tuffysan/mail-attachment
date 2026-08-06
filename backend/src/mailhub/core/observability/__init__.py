"""Structured logging and request-context utilities."""

from mailhub.core.observability.context import (
    correlation_id_var,
    get_correlation_id,
    get_request_id,
    request_id_var,
)
from mailhub.core.observability.logging import configure_logging

__all__ = [
    "configure_logging",
    "correlation_id_var",
    "get_correlation_id",
    "get_request_id",
    "request_id_var",
]
