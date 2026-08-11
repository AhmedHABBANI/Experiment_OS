"""API error handling."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from experiment_os_stats import ExperimentOSError


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


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a stable API error payload."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
