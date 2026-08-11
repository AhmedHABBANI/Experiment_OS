"""Non-parametric analyses for independent A/B samples."""

import numpy as np
from scipy.stats import mannwhitneyu

from experiment_os_stats.analyses._common import validate_alpha
from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples
from experiment_os_stats.exceptions import DegenerateSampleError
from experiment_os_stats.results import StatisticalResult, StatisticalWarning
from experiment_os_stats.types import Alternative, MetricType, MissingValuePolicy, WarningSeverity


def mann_whitney_u_test(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    alpha: float = 0.05,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Run a two-sided Mann-Whitney U test with rank effects oriented B versus A.

    The returned U statistic is computed for group B. The rank-biserial effect is
    positive when observations from B tend to rank above observations from A.
    """
    validate_alpha(alpha)
    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.CONTINUOUS,
        missing_policy=missing_policy,
        minimum_size=1,
    )
    values_a = validated.group_a.values
    values_b = validated.group_b.values
    n_a = int(values_a.size)
    n_b = int(values_b.size)
    combined_values = np.concatenate((values_a, values_b))

    if np.unique(combined_values).size == 1:
        raise DegenerateSampleError(
            "Mann-Whitney U requires at least two distinct combined observations.",
            details={
                "n_a": n_a,
                "n_b": n_b,
                "unique_count": 1,
            },
        )

    ties_present = np.unique(combined_values).size < combined_values.size
    reference = mannwhitneyu(
        values_b,
        values_a,
        alternative=Alternative.TWO_SIDED.value,
        method="auto",
    )
    statistic = float(reference.statistic)
    pair_count = n_a * n_b
    probability_of_superiority = statistic / pair_count
    rank_biserial = 2 * probability_of_superiority - 1
    warnings = [
        StatisticalWarning(
            code="MANN_WHITNEY_NOT_MEDIAN_TEST",
            message=(
                "Mann-Whitney U does not automatically test a difference in medians; "
                "that interpretation requires additional distribution-shape assumptions."
            ),
            severity=WarningSeverity.INFO,
        )
    ]
    if ties_present:
        warnings.append(
            StatisticalWarning(
                code="TIES_PRESENT",
                message=(
                    "The combined sample contains tied values; SciPy's automatic method "
                    "accounts for ties with its asymptotic calculation when required."
                ),
                severity=WarningSeverity.INFO,
                details={
                    "combined_size": int(combined_values.size),
                    "unique_count": int(np.unique(combined_values).size),
                },
            )
        )

    return StatisticalResult(
        test_name="mann_whitney_u_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=statistic,
        p_value=float(reference.pvalue),
        alpha=alpha,
        alternative=Alternative.TWO_SIDED,
        effect_size=rank_biserial,
        effect_size_name="rank_biserial_correlation",
        assumptions=(
            "The two groups contain independent observations.",
            "The outcome is at least ordinal.",
            "Observations can be ranked meaningfully across groups.",
        ),
        warnings=tuple(warnings),
        interpretation={
            "null_hypothesis": (
                "A randomly selected observation from group B is equally likely to rank "
                "above or below one from group A."
            ),
            "alternative_hypothesis": ("The distributions of ranks differ between groups A and B."),
            "effect_direction": (
                "Positive rank-biserial values favor higher ranks in group B; negative "
                "values favor higher ranks in group A."
            ),
        },
        metadata={
            "n_a": n_a,
            "n_b": n_b,
            "u_statistic_group": "group_b",
            "probability_of_superiority_b_over_a": probability_of_superiority,
            "effect_direction": "group_b_relative_to_group_a",
            "method": "auto",
            "ties_present": ties_present,
        },
    )
