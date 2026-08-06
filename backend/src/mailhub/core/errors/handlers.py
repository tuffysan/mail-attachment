import logging
from http import HTTPStatus
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from mailhub.core.errors.exceptions import ApplicationError
from mailhub.core.errors.problem import ProblemDetails
from mailhub.core.observability.context import get_request_id

logger = logging.getLogger(__name__)


def _resolve_request_id(request: Request) -> str:
    return (
        get_request_id()
        or getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
        or str(uuid4())
    )


def _problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _resolve_request_id(request)
    problem = ProblemDetails(
        title=title,
        status=status_code,
        detail=detail,
        instance=request.url.path,
        code=code,
        request_id=request_id,
        errors=errors,
    )
    response_headers = dict(headers or {})
    response_headers.setdefault("X-Request-ID", request_id)
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
        headers=response_headers,
    )


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    logger.info(
        "application_error",
        extra={
            "event": "application_error",
            "error_code": exc.error_code,
            "status_code": exc.http_status,
            "path": request.url.path,
            "context": exc.context,
        },
    )
    return _problem_response(
        request,
        status_code=exc.http_status,
        title=exc.error_title,
        detail=exc.detail,
        code=exc.error_code,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors: list[dict[str, Any]] = []
    for item in exc.errors():
        errors.append(
            {
                "location": [str(part) for part in item.get("loc", ())],
                "message": item.get("msg", "Invalid value"),
                "type": item.get("type", "validation_error"),
            }
        )
    return _problem_response(
        request,
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        title="Request validation failed",
        detail="One or more request values are invalid.",
        code="request_validation_error",
        errors=errors,
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
    title = (
        HTTPStatus(exc.status_code).phrase
        if exc.status_code in HTTPStatus._value2member_map_
        else "HTTP error"
    )
    return _problem_response(
        request,
        status_code=exc.status_code,
        title=title,
        detail=detail,
        code=f"http_{exc.status_code}",
        headers=exc.headers,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_request_error",
        extra={
            "event": "unhandled_request_error",
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )
    return _problem_response(
        request,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        title="Internal server error",
        detail="An unexpected error occurred. Use the request ID when contacting support.",
        code="internal_server_error",
    )


def install_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers in most-specific-first order."""

    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
