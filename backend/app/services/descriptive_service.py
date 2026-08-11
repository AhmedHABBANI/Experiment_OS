"""Descriptive-statistics service functions."""

from app.schemas.descriptive import (
    BinaryDescriptiveRequest,
    ContinuousDescriptiveRequest,
    DescriptiveResponse,
)
from experiment_os_stats import MissingValuePolicy, summarize_binary_ab, summarize_continuous_ab


def run_binary_descriptive_summary(request: BinaryDescriptiveRequest) -> DescriptiveResponse:
    """Run binary descriptive statistics using the statistics package."""
    result = summarize_binary_ab(
        request.group_a,
        request.group_b,
        confidence_level=request.confidence_level,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return DescriptiveResponse(**result.to_dict())


def run_continuous_descriptive_summary(
    request: ContinuousDescriptiveRequest,
) -> DescriptiveResponse:
    """Run continuous descriptive statistics using the statistics package."""
    result = summarize_continuous_ab(
        request.group_a,
        request.group_b,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return DescriptiveResponse(**result.to_dict())
