"""Aggregate versioned API routers."""

from fastapi import APIRouter

from app.api.v1.analyses import router as analyses_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.descriptive import router as descriptive_router
from app.api.v1.diagnostics import router as diagnostics_router
from app.api.v1.health import router as health_router
from app.api.v1.simulations import router as simulations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analyses_router, prefix="/analyses", tags=["analyses"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
api_router.include_router(descriptive_router, prefix="/descriptive", tags=["descriptive"])
api_router.include_router(diagnostics_router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(simulations_router, prefix="/simulations", tags=["simulations"])
