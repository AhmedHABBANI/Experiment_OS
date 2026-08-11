"""FastAPI application factory for ExperimentOS."""

from fastapi import FastAPI

from app.api.router import api_router
from app.errors import register_exception_handlers


def create_app() -> FastAPI:
    """Create and configure the ExperimentOS API application."""
    app = FastAPI(
        title="ExperimentOS API",
        version="0.1.0",
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
