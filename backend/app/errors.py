"""API error handling."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from experiment_os_stats import ExperimentOSError


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


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a stable API error payload."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
