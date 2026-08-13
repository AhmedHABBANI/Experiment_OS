"""Statistical-analysis service functions."""

from app.schemas.analyses import (
    BinaryAnalysisRequest,
    ContinuousAnalysisRequest,
    StatisticalAnalysisResponse,
)
from experiment_os_stats import (
    Alternative,
    MissingValuePolicy,
    fisher_exact_test,
    student_t_test,
    two_proportion_z_test,
)


def run_two_proportion_z_analysis(
    request: BinaryAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run the two-proportion z-test using the statistics package."""
    result = two_proportion_z_test(
        request.group_a,
        request.group_b,
        alpha=request.alpha,
        alternative=Alternative(request.alternative),
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())


def run_fisher_exact_analysis(
    request: BinaryAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run Fisher's exact test using the statistics package."""
    result = fisher_exact_test(
        request.group_a,
        request.group_b,
        alpha=request.alpha,
        alternative=Alternative(request.alternative),
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())


def run_student_t_analysis(
    request: ContinuousAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run Student's independent two-sample t-test using the statistics package."""
    result = student_t_test(
        request.group_a,
        request.group_b,
        alpha=request.alpha,
        alternative=Alternative(request.alternative),
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())
