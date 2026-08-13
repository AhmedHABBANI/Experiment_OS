"""Statistical-analysis service functions."""

from app.schemas.analyses import (
    BinaryAnalysisRequest,
    BootstrapAnalysisRequest,
    ContinuousAnalysisRequest,
    MannWhitneyAnalysisRequest,
    PermutationAnalysisRequest,
    StatisticalAnalysisResponse,
)
from experiment_os_stats import (
    Alternative,
    MissingValuePolicy,
    bootstrap_mean_difference,
    bootstrap_median_difference,
    fisher_exact_test,
    mann_whitney_u_test,
    permutation_mean_test,
    student_t_test,
    two_proportion_z_test,
    welch_t_test,
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


def run_welch_t_analysis(
    request: ContinuousAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run Welch's independent two-sample t-test using the statistics package."""
    result = welch_t_test(
        request.group_a,
        request.group_b,
        alpha=request.alpha,
        alternative=Alternative(request.alternative),
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())


def run_mann_whitney_analysis(
    request: MannWhitneyAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run the two-sided Mann-Whitney U test using the statistics package."""
    result = mann_whitney_u_test(
        request.group_a,
        request.group_b,
        alpha=request.alpha,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())


def run_permutation_analysis(
    request: PermutationAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Run the Monte-Carlo permutation mean test using the statistics package."""
    result = permutation_mean_test(
        request.group_a,
        request.group_b,
        alpha=request.alpha,
        alternative=Alternative(request.alternative),
        n_permutations=request.n_permutations,
        seed=request.seed,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())


def run_bootstrap_analysis(
    request: BootstrapAnalysisRequest,
) -> StatisticalAnalysisResponse:
    """Estimate a bootstrap mean or median difference using the statistics package."""
    procedure = (
        bootstrap_mean_difference if request.estimand == "mean" else bootstrap_median_difference
    )
    result = procedure(
        request.group_a,
        request.group_b,
        confidence_level=request.confidence_level,
        n_resamples=request.n_resamples,
        seed=request.seed,
        missing_policy=MissingValuePolicy(request.missing_policy),
    )
    return StatisticalAnalysisResponse(**result.to_dict())
