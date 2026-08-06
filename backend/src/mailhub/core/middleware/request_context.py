import logging
import re
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from mailhub.core.observability.context import correlation_id_var, request_id_var

logger = logging.getLogger("mailhub.http")
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _header(scope: Scope, name: str) -> str | None:
    target = name.lower().encode("latin-1")
    for key, value in scope.get("headers", []):
        if key.lower() == target:
            decoded = value.decode("latin-1").strip()
            return decoded if _SAFE_IDENTIFIER.fullmatch(decoded) else None
    return None


class RequestContextMiddleware:
    """Create request context, response headers and one structured access log."""

    def __init__(
        self,
        app: ASGIApp,
        request_id_header: str = "X-Request-ID",
        correlation_id_header: str = "X-Correlation-ID",
        excluded_paths: set[str] | None = None,
    ) -> None:
        self.app = app
        self.request_id_header = request_id_header
        self.correlation_id_header = correlation_id_header
        self.excluded_paths = excluded_paths or set()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _header(scope, self.request_id_header) or str(uuid4())
        correlation_id = _header(scope, self.correlation_id_header) or request_id
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        state["correlation_id"] = correlation_id
        request_token = request_id_var.set(request_id)
        correlation_token = correlation_id_var.set(correlation_id)
        started = time.perf_counter()
        status_code = 500

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (self.request_id_header.encode("latin-1"), request_id.encode("latin-1")),
                        (self.correlation_id_header.encode("latin-1"), correlation_id.encode("latin-1")),
                    ]
                )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            path = scope.get("path", "")
            if path not in self.excluded_paths:
                client = scope.get("client")
                logger.info(
                    "http_request_completed",
                    extra={
                        "http_method": scope.get("method"),
                        "http_path": path,
                        "http_status": status_code,
                        "duration_ms": duration_ms,
                        "client_ip": client[0] if client else None,
                    },
                )
            request_id_var.reset(request_token)
            correlation_id_var.reset(correlation_token)
