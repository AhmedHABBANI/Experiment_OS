"""Resampling-based analyses for independent A/B samples."""

from collections.abc import Callable

import numpy as np

from experiment_os_stats.analyses._common import normalize_alternative, validate_alpha
from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples
from experiment_os_stats.exceptions import DegenerateSampleError, InvalidParameterError
from experiment_os_stats.interpretation import interpret_permutation_mean_result
from experiment_os_stats.results import ConfidenceInterval, StatisticalResult
from experiment_os_stats.types import Alternative, MetricType, MissingValuePolicy

_MIN_RESAMPLES = 100
_MAX_RESAMPLES = 100_000


def _validate_resample_count(value: int, *, parameter_name: str) -> None:
    """Validate a bounded integer resampling count."""
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not _MIN_RESAMPLES <= value <= _MAX_RESAMPLES
    ):
        raise InvalidParameterError(
            f"{parameter_name} must be an integer between 100 and 100000.",
            details={
                parameter_name: value,
                "minimum": _MIN_RESAMPLES,
                "maximum": _MAX_RESAMPLES,
            },
        )


def _validate_seed(seed: int | None) -> None:
    """Validate an optional non-negative random seed."""
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or seed < 0):
        raise InvalidParameterError(
            "seed must be a non-negative integer or None.",
            details={"seed": seed},
        )


def _validate_confidence_level(confidence_level: float) -> None:
    """Validate a confidence level for interval estimation."""
    if (
        isinstance(confidence_level, bool)
        or not isinstance(confidence_level, int | float)
        or not 0 < confidence_level < 1
    ):
        raise InvalidParameterError(
            "confidence_level must be strictly between zero and one.",
            details={"confidence_level": confidence_level},
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


def _bootstrap_statistic_difference(
    values_a: np.ndarray,
    values_b: np.ndarray,
    *,
    statistic: Callable[[np.ndarray], float],
    n_resamples: int,
    confidence_level: float,
    seed: int | None,
) -> tuple[float, np.ndarray, float, float, float]:
    """Bootstrap a B-minus-A statistic and return estimate, distribution, SE, and bounds."""
    n_a = int(values_a.size)
    n_b = int(values_b.size)
    estimate = float(statistic(values_b) - statistic(values_a))
    bootstrap_distribution = np.empty(n_resamples, dtype=float)
    rng = np.random.default_rng(seed)

    for index in range(n_resamples):
        resampled_a = rng.choice(values_a, size=n_a, replace=True)
        resampled_b = rng.choice(values_b, size=n_b, replace=True)
        bootstrap_distribution[index] = float(statistic(resampled_b) - statistic(resampled_a))

    tail_probability = (1 - confidence_level) / 2
    lower, upper = np.quantile(
        bootstrap_distribution,
        [tail_probability, 1 - tail_probability],
    )
    standard_error = float(np.std(bootstrap_distribution, ddof=1))
    return (
        estimate,
        bootstrap_distribution,
        standard_error,
        float(lower),
        float(upper),
    )


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
    _validate_resample_count(n_permutations, parameter_name="n_permutations")
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
        interpretation=interpret_permutation_mean_result(
            estimate=observed_statistic,
            p_value=p_value,
            alpha=alpha,
            alternative=normalized_alternative,
            n_permutations=n_permutations,
            seed=seed,
        ),
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


def bootstrap_mean_difference(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    confidence_level: float = 0.95,
    n_resamples: int = 10_000,
    seed: int | None = None,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Estimate the independent mean difference B minus A by percentile bootstrap.

    Each group is resampled independently with replacement. A fixed seed reproduces
    the bootstrap distribution, standard error, and percentile interval.
    """
    _validate_confidence_level(confidence_level)
    _validate_resample_count(n_resamples, parameter_name="n_resamples")
    _validate_seed(seed)
    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.CONTINUOUS,
        missing_policy=missing_policy,
        minimum_size=2,
    )

    values_a = validated.group_a.values
    values_b = validated.group_b.values
    n_a = int(values_a.size)
    n_b = int(values_b.size)
    estimate, bootstrap_distribution, standard_error, lower, upper = (
        _bootstrap_statistic_difference(
            values_a,
            values_b,
            statistic=np.mean,
            n_resamples=n_resamples,
            confidence_level=confidence_level,
            seed=seed,
        )
    )

    return StatisticalResult(
        test_name="bootstrap_mean_difference",
        metric_type=MetricType.CONTINUOUS,
        alpha=1 - confidence_level,
        alternative=Alternative.TWO_SIDED,
        estimate=estimate,
        confidence_interval=ConfidenceInterval(
            lower=lower,
            upper=upper,
            level=confidence_level,
            parameter="difference_in_means_b_minus_a",
            method="bootstrap_percentile",
        ),
        assumptions=(
            "The two groups contain independent observations.",
            "Observations within each group are representative and identically distributed.",
            "The empirical group distributions approximate their populations.",
        ),
        interpretation={
            "estimand": "The population mean difference, group B minus group A.",
            "interval": (
                "The percentile interval describes bootstrap uncertainty around the "
                "estimated mean difference."
            ),
        },
        metadata={
            "n_a": n_a,
            "n_b": n_b,
            "difference_direction": "group_b_minus_group_a",
            "n_resamples": n_resamples,
            "seed": seed,
            "standard_error": standard_error,
            "interval_method": "percentile",
            "bootstrap_distribution": [float(value) for value in bootstrap_distribution],
        },
    )


def bootstrap_median_difference(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    confidence_level: float = 0.95,
    n_resamples: int = 10_000,
    seed: int | None = None,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Estimate the independent median difference B minus A by percentile bootstrap.

    Each group is resampled independently with replacement. A fixed seed reproduces
    the bootstrap distribution, standard error, and percentile interval.
    """
    _validate_confidence_level(confidence_level)
    _validate_resample_count(n_resamples, parameter_name="n_resamples")
    _validate_seed(seed)
    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.CONTINUOUS,
        missing_policy=missing_policy,
        minimum_size=2,
    )

    values_a = validated.group_a.values
    values_b = validated.group_b.values
    n_a = int(values_a.size)
    n_b = int(values_b.size)
    estimate, bootstrap_distribution, standard_error, lower, upper = (
        _bootstrap_statistic_difference(
            values_a,
            values_b,
            statistic=np.median,
            n_resamples=n_resamples,
            confidence_level=confidence_level,
            seed=seed,
        )
    )

    return StatisticalResult(
        test_name="bootstrap_median_difference",
        metric_type=MetricType.CONTINUOUS,
        alpha=1 - confidence_level,
        alternative=Alternative.TWO_SIDED,
        estimate=estimate,
        confidence_interval=ConfidenceInterval(
            lower=lower,
            upper=upper,
            level=confidence_level,
            parameter="difference_in_medians_b_minus_a",
            method="bootstrap_percentile",
        ),
        assumptions=(
            "The two groups contain independent observations.",
            "Observations within each group are representative and identically distributed.",
            "The empirical group distributions approximate their populations.",
        ),
        interpretation={
            "estimand": "The population median difference, group B minus group A.",
            "interval": (
                "The percentile interval describes bootstrap uncertainty around the "
                "estimated median difference."
            ),
        },
        metadata={
            "n_a": n_a,
            "n_b": n_b,
            "difference_direction": "group_b_minus_group_a",
            "n_resamples": n_resamples,
            "seed": seed,
            "standard_error": standard_error,
            "interval_method": "percentile",
            "bootstrap_distribution": [float(value) for value in bootstrap_distribution],
        },
    )
