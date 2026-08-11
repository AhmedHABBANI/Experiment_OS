"""Descriptive-statistics endpoints."""

from fastapi import APIRouter

from app.schemas.descriptive import (
    BinaryDescriptiveRequest,
    ContinuousDescriptiveRequest,
    DescriptiveResponse,
)
from app.services.descriptive_service import (
    run_binary_descriptive_summary,
    run_continuous_descriptive_summary,
)

router = APIRouter()


@router.post("/binary", response_model=DescriptiveResponse)
def summarize_binary(request: BinaryDescriptiveRequest) -> DescriptiveResponse:
    """Summarize a binary A/B dataset."""
    return run_binary_descriptive_summary(request)


@router.post("/continuous", response_model=DescriptiveResponse)
def summarize_continuous(request: ContinuousDescriptiveRequest) -> DescriptiveResponse:
    """Summarize a continuous A/B dataset."""
    return run_continuous_descriptive_summary(request)
