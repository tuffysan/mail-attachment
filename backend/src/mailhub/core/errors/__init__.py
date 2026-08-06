"""Central application exceptions and FastAPI exception handlers."""

from mailhub.core.errors.exceptions import (
    ApplicationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from mailhub.core.errors.handlers import install_exception_handlers
from mailhub.core.errors.problem import ProblemDetails

__all__ = [
    "ApplicationError",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "ProblemDetails",
    "ServiceUnavailableError",
    "UnauthorizedError",
    "ValidationError",
    "install_exception_handlers",
]
