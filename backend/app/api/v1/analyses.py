"""Statistical-analysis endpoints."""

from fastapi import APIRouter

from app.schemas.analyses import BinaryAnalysisRequest, StatisticalAnalysisResponse
from app.services.analysis_service import (
    run_fisher_exact_analysis,
    run_two_proportion_z_analysis,
)

router = APIRouter()


@router.post("/two-proportion-z", response_model=StatisticalAnalysisResponse)
def analyze_two_proportion_z(
    request: BinaryAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Test equality of two independent binary proportions."""
    return run_two_proportion_z_analysis(request)


@router.post("/fisher-exact", response_model=StatisticalAnalysisResponse)
def analyze_fisher_exact(
    request: BinaryAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run Fisher's exact test on two independent binary groups."""
    return run_fisher_exact_analysis(request)
