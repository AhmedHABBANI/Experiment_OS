"""API error handling."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from experiment_os_stats import ExperimentOSError

logger = logging.getLogger(__name__)


class DatasetUploadError(Exception):
    """Structured error raised while validating an uploaded dataset."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ) -> None:
        """Initialize a safe dataset error with a stable API code."""
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Register structured API exception handlers."""

    @app.exception_handler(ExperimentOSError)
    async def handle_experiment_os_error(
        _request: Request,
        error: ExperimentOSError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": error.to_dict()},
        )

    @app.exception_handler(DatasetUploadError)
    async def handle_dataset_upload_error(
        _request: Request,
        error: DatasetUploadError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=error_payload(error.code, error.message, error.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        controlled_errors = [
            {
                "location": [str(part) for part in item["loc"]],
                "message": item["msg"],
                "type": item["type"],
            }
            for item in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_payload(
                "INVALID_REQUEST",
                "The request does not match the expected API contract.",
                {"errors": controlled_errors},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error(
            "Unhandled API error on %s %s",
            request.method,
            request.url.path,
            exc_info=(type(error), error, error.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content=error_payload(
                "INTERNAL_ERROR",
                "An unexpected internal error occurred.",
            ),
        )


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a stable API error payload."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
