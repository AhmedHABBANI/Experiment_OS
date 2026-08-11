"""Diagnostic-visualization endpoints."""

from fastapi import APIRouter

from app.schemas.diagnostics import (
    BinaryDiagnosticsRequest,
    BinaryDiagnosticsResponse,
    ContinuousDiagnosticsRequest,
    ContinuousDiagnosticsResponse,
)
from app.services.diagnostics_service import (
    build_binary_diagnostics,
    build_continuous_diagnostics,
)

router = APIRouter()


@router.post("/binary-rate", response_model=BinaryDiagnosticsResponse)
def binary_rate_diagnostics(
    request: BinaryDiagnosticsRequest,
) -> BinaryDiagnosticsResponse:
    """Return binary rates and confidence intervals for A/B plotting."""
    return build_binary_diagnostics(request)


@router.post("/continuous-distribution", response_model=ContinuousDiagnosticsResponse)
def continuous_distribution_diagnostics(
    request: ContinuousDiagnosticsRequest,
) -> ContinuousDiagnosticsResponse:
    """Return histogram, boxplot and normal QQ data for A/B plotting."""
    return build_continuous_diagnostics(request)
