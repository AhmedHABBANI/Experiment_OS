"""Diagnostic-visualization service functions."""

from app.schemas.diagnostics import (
    BinaryDiagnosticsRequest,
    BinaryDiagnosticsResponse,
    ContinuousDiagnosticsRequest,
    ContinuousDiagnosticsResponse,
)
from experiment_os_stats import (
    MissingValuePolicy,
    binary_rate_plot_data,
    continuous_distribution_plot_data,
)


def build_binary_diagnostics(
    request: BinaryDiagnosticsRequest,
) -> BinaryDiagnosticsResponse:
    """Build binary plot data using the statistics package."""
    result = binary_rate_plot_data(
        request.group_a,
        request.group_b,
        confidence_level=request.confidence_level,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return BinaryDiagnosticsResponse(**result.to_dict())


def build_continuous_diagnostics(
    request: ContinuousDiagnosticsRequest,
) -> ContinuousDiagnosticsResponse:
    """Build continuous plot data using the statistics package."""
    result = continuous_distribution_plot_data(
        request.group_a,
        request.group_b,
        bins=request.bins,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return ContinuousDiagnosticsResponse(**result.to_dict())
