"""Resampling-based analyses for independent A/B samples."""

import numpy as np

from experiment_os_stats.analyses._common import normalize_alternative, validate_alpha
from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples
from experiment_os_stats.exceptions import DegenerateSampleError, InvalidParameterError
from experiment_os_stats.results import StatisticalResult
from experiment_os_stats.types import Alternative, MetricType, MissingValuePolicy

_MIN_PERMUTATIONS = 100
_MAX_PERMUTATIONS = 100_000


def _validate_permutation_count(n_permutations: int) -> None:
    """Validate a bounded Monte-Carlo permutation count."""
    if (
        isinstance(n_permutations, bool)
        or not isinstance(n_permutations, int)
        or not _MIN_PERMUTATIONS <= n_permutations <= _MAX_PERMUTATIONS
    ):
        raise InvalidParameterError(
            "n_permutations must be an integer between 100 and 100000.",
            details={
                "n_permutations": n_permutations,
                "minimum": _MIN_PERMUTATIONS,
                "maximum": _MAX_PERMUTATIONS,
            },
        )


def _validate_seed(seed: int | None) -> None:
    """Validate an optional non-negative random seed."""
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or seed < 0):
        raise InvalidParameterError(
            "seed must be a non-negative integer or None.",
            details={"seed": seed},
        )


def _count_extreme_statistics(
    null_distribution: np.ndarray,
    observed_statistic: float,
    alternative: Alternative,
) -> int:
    """Count permutation statistics at least as extreme as the observation."""
    if alternative is Alternative.GREATER:
        return int(np.sum(null_distribution >= observed_statistic))
    if alternative is Alternative.LESS:
        return int(np.sum(null_distribution <= observed_statistic))
    return int(np.sum(np.abs(null_distribution) >= abs(observed_statistic)))


def permutation_mean_test(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    alpha: float = 0.05,
    alternative: Alternative | str = Alternative.TWO_SIDED,
    n_permutations: int = 10_000,
    seed: int | None = None,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Test a mean difference by Monte-Carlo permutation, oriented B minus A.

    The empirical p-value uses the add-one correction, so a finite permutation
    sample never reports a zero p-value. A fixed seed reproduces the null distribution.
    """
    validate_alpha(alpha)
    normalized_alternative = normalize_alternative(alternative)
    _validate_permutation_count(n_permutations)
    _validate_seed(seed)
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
    pooled_values = np.concatenate((values_a, values_b))
    if np.unique(pooled_values).size == 1:
        raise DegenerateSampleError(
            "The permutation test requires variation in the combined observations.",
            details={"n_a": n_a, "n_b": n_b, "unique_count": 1},
        )

    observed_statistic = float(np.mean(values_b) - np.mean(values_a))
    null_distribution = np.empty(n_permutations, dtype=float)
    rng = np.random.default_rng(seed)
    for index in range(n_permutations):
        permuted = rng.permutation(pooled_values)
        null_distribution[index] = float(np.mean(permuted[n_a:]) - np.mean(permuted[:n_a]))

    extreme_count = _count_extreme_statistics(
        null_distribution,
        observed_statistic,
        normalized_alternative,
    )
    p_value = (extreme_count + 1) / (n_permutations + 1)

    return StatisticalResult(
        test_name="permutation_mean_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=observed_statistic,
        p_value=p_value,
        alpha=alpha,
        alternative=normalized_alternative,
        estimate=observed_statistic,
        assumptions=(
            "The two groups contain independent observations.",
            "Group labels are exchangeable under the null hypothesis.",
            "The mean difference is an appropriate effect summary.",
        ),
        interpretation={
            "null_hypothesis": (
                "Group labels are exchangeable and the population mean difference is zero."
            ),
            "alternative_hypothesis": (
                "The population mean in group B differs from group A."
                if normalized_alternative is Alternative.TWO_SIDED
                else (
                    "The population mean in group B is "
                    f"{normalized_alternative.value} than group A."
                )
            ),
        },
        metadata={
            "n_a": n_a,
            "n_b": n_b,
            "difference_direction": "group_b_minus_group_a",
            "n_permutations": n_permutations,
            "seed": seed,
            "extreme_count": extreme_count,
            "p_value_method": "add_one_monte_carlo",
            "null_distribution": [float(value) for value in null_distribution],
        },
    )
