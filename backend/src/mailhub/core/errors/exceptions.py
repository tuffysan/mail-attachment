from http import HTTPStatus
from typing import Any


class ApplicationError(Exception):
    """Base exception for expected application-level failures."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    code = "application_error"
    title = "Application error"

    def __init__(
        self,
        detail: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        title: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.error_code = code or self.code
        self.http_status = int(status_code or self.status_code)
        self.error_title = title or self.title
        self.context = context or {}


class ValidationError(ApplicationError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "validation_error"
    title = "Validation failed"


class UnauthorizedError(ApplicationError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "unauthorized"
    title = "Authentication required"


class ForbiddenError(ApplicationError):
    status_code = HTTPStatus.FORBIDDEN
    code = "forbidden"
    title = "Access denied"


class NotFoundError(ApplicationError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"
    title = "Resource not found"


class ConflictError(ApplicationError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"
    title = "Resource conflict"


class ServiceUnavailableError(ApplicationError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "service_unavailable"
    title = "Service unavailable"
