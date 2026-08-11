"""Frequentist analyses for independent continuous A/B samples."""

from math import sqrt

import numpy as np
from scipy.stats import t

from experiment_os_stats.analyses._common import normalize_alternative, validate_alpha
from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples
from experiment_os_stats.exceptions import DegenerateSampleError
from experiment_os_stats.results import ConfidenceInterval, StatisticalResult, StatisticalWarning
from experiment_os_stats.types import Alternative, MetricType, MissingValuePolicy, WarningSeverity

_SAMPLE_SIZE_IMBALANCE_RATIO = 4.0
_IQR_OUTLIER_MULTIPLIER = 1.5


def _p_value(statistic: float, degrees_of_freedom: int, alternative: Alternative) -> float:
    """Compute a Student-reference p-value for the selected alternative."""
    if alternative is Alternative.GREATER:
        return float(t.sf(statistic, degrees_of_freedom))
    if alternative is Alternative.LESS:
        return float(t.cdf(statistic, degrees_of_freedom))
    return float(2 * t.sf(abs(statistic), degrees_of_freedom))


def _iqr_outlier_details(values: np.ndarray) -> dict[str, float | int] | None:
    """Return Tukey-fence outlier details when a sample contains outliers."""
    q1, q3 = np.quantile(values, [0.25, 0.75])
    iqr = float(q3 - q1)
    lower_fence = float(q1 - _IQR_OUTLIER_MULTIPLIER * iqr)
    upper_fence = float(q3 + _IQR_OUTLIER_MULTIPLIER * iqr)
    outlier_count = int(np.sum((values < lower_fence) | (values > upper_fence)))

    if outlier_count == 0:
        return None

    return {
        "outlier_count": outlier_count,
        "lower_fence": lower_fence,
        "upper_fence": upper_fence,
        "iqr": iqr,
        "multiplier": _IQR_OUTLIER_MULTIPLIER,
    }


def _continuous_warnings(
    values_a: np.ndarray,
    values_b: np.ndarray,
) -> tuple[StatisticalWarning, ...]:
    """Build structured diagnostics shared by continuous parametric tests."""
    n_a = int(values_a.size)
    n_b = int(values_b.size)
    size_ratio = max(n_a, n_b) / min(n_a, n_b)
    warnings: list[StatisticalWarning] = []

    if size_ratio >= _SAMPLE_SIZE_IMBALANCE_RATIO:
        warnings.append(
            StatisticalWarning(
                code="IMBALANCED_SAMPLE_SIZES",
                message=(
                    "Group sample sizes are strongly imbalanced; precision and sensitivity "
                    "to assumption violations may differ between groups."
                ),
                severity=WarningSeverity.WARNING,
                details={
                    "n_a": n_a,
                    "n_b": n_b,
                    "size_ratio": size_ratio,
                    "warning_threshold": _SAMPLE_SIZE_IMBALANCE_RATIO,
                },
            )
        )

    outlier_groups = {
        group: details
        for group, values in (("group_a", values_a), ("group_b", values_b))
        if (details := _iqr_outlier_details(values)) is not None
    }
    if outlier_groups:
        warnings.append(
            StatisticalWarning(
                code="IQR_OUTLIERS_DETECTED",
                message=(
                    "At least one observation lies outside the 1.5 IQR Tukey fences; "
                    "mean-based inference may be sensitive to these observations."
                ),
                severity=WarningSeverity.WARNING,
                details={"groups": outlier_groups},
            )
        )

    return tuple(warnings)


def student_t_test(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    alpha: float = 0.05,
    alternative: Alternative | str = Alternative.TWO_SIDED,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Run Student's independent two-sample t-test with effects oriented B minus A.

    Population variances are assumed equal and estimated with the pooled sample
    variance. The confidence interval is always a two-sided ``1 - alpha`` interval.
    """
    validate_alpha(alpha)
    normalized_alternative = normalize_alternative(alternative)
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
    mean_a = float(np.mean(values_a))
    mean_b = float(np.mean(values_b))
    variance_a = float(np.var(values_a, ddof=1))
    variance_b = float(np.var(values_b, ddof=1))
    degrees_of_freedom = n_a + n_b - 2
    pooled_variance = ((n_a - 1) * variance_a + (n_b - 1) * variance_b) / degrees_of_freedom

    if pooled_variance == 0:
        raise DegenerateSampleError(
            "The pooled variance is zero, so the Student t statistic is undefined.",
            details={
                "variance_a": variance_a,
                "variance_b": variance_b,
                "n_a": n_a,
                "n_b": n_b,
            },
        )

    difference = mean_b - mean_a
    pooled_standard_deviation = sqrt(pooled_variance)
    standard_error = pooled_standard_deviation * sqrt(1 / n_a + 1 / n_b)
    statistic = difference / standard_error
    critical_value = float(t.ppf(1 - alpha / 2, degrees_of_freedom))

    return StatisticalResult(
        test_name="student_t_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=float(statistic),
        p_value=_p_value(statistic, degrees_of_freedom, normalized_alternative),
        alpha=alpha,
        alternative=normalized_alternative,
        estimate=difference,
        confidence_interval=ConfidenceInterval(
            lower=difference - critical_value * standard_error,
            upper=difference + critical_value * standard_error,
            level=1 - alpha,
            parameter="difference_in_means_b_minus_a",
            method="student_t_pooled",
        ),
        effect_size=difference / pooled_standard_deviation,
        effect_size_name="cohens_d",
        assumptions=(
            "The two groups contain independent observations.",
            "The outcome is continuous in both groups.",
            "The population variances are equal.",
            "The group means are approximately normally distributed.",
        ),
        warnings=_continuous_warnings(values_a, values_b),
        interpretation={
            "null_hypothesis": "The population means in groups A and B are equal.",
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
            "mean_a": mean_a,
            "mean_b": mean_b,
            "variance_a": variance_a,
            "variance_b": variance_b,
            "pooled_variance": pooled_variance,
            "standard_error": standard_error,
            "degrees_of_freedom": degrees_of_freedom,
            "difference_direction": "group_b_minus_group_a",
        },
    )


def welch_t_test(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    alpha: float = 0.05,
    alternative: Alternative | str = Alternative.TWO_SIDED,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Run Welch's independent two-sample t-test with effects oriented B minus A.

    Group variances are estimated separately. Degrees of freedom use the
    Welch-Satterthwaite approximation, and the confidence interval is always a
    two-sided ``1 - alpha`` interval. Cohen's d is a descriptive standardized
    effect based on the pooled sample standard deviation; it is not used by the test.
    """
    validate_alpha(alpha)
    normalized_alternative = normalize_alternative(alternative)
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
    mean_a = float(np.mean(values_a))
    mean_b = float(np.mean(values_b))
    variance_a = float(np.var(values_a, ddof=1))
    variance_b = float(np.var(values_b, ddof=1))
    variance_term_a = variance_a / n_a
    variance_term_b = variance_b / n_b
    standard_error_squared = variance_term_a + variance_term_b

    if standard_error_squared == 0:
        raise DegenerateSampleError(
            "The Welch standard error is zero, so the t statistic is undefined.",
            details={
                "variance_a": variance_a,
                "variance_b": variance_b,
                "n_a": n_a,
                "n_b": n_b,
            },
        )

    degrees_of_freedom = standard_error_squared**2 / (
        variance_term_a**2 / (n_a - 1) + variance_term_b**2 / (n_b - 1)
    )
    difference = mean_b - mean_a
    standard_error = sqrt(standard_error_squared)
    statistic = difference / standard_error
    critical_value = float(t.ppf(1 - alpha / 2, degrees_of_freedom))
    pooled_variance = ((n_a - 1) * variance_a + (n_b - 1) * variance_b) / (n_a + n_b - 2)

    return StatisticalResult(
        test_name="welch_t_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=float(statistic),
        p_value=_p_value(statistic, degrees_of_freedom, normalized_alternative),
        alpha=alpha,
        alternative=normalized_alternative,
        estimate=difference,
        confidence_interval=ConfidenceInterval(
            lower=difference - critical_value * standard_error,
            upper=difference + critical_value * standard_error,
            level=1 - alpha,
            parameter="difference_in_means_b_minus_a",
            method="welch_t",
        ),
        effect_size=difference / sqrt(pooled_variance),
        effect_size_name="cohens_d",
        assumptions=(
            "The two groups contain independent observations.",
            "The outcome is continuous in both groups.",
            "The group means are approximately normally distributed.",
            "Equal population variances are not assumed.",
        ),
        warnings=_continuous_warnings(values_a, values_b),
        interpretation={
            "null_hypothesis": "The population means in groups A and B are equal.",
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
            "mean_a": mean_a,
            "mean_b": mean_b,
            "variance_a": variance_a,
            "variance_b": variance_b,
            "pooled_variance_for_effect_size": pooled_variance,
            "standard_error": standard_error,
            "degrees_of_freedom": degrees_of_freedom,
            "degrees_of_freedom_method": "welch_satterthwaite",
            "difference_direction": "group_b_minus_group_a",
        },
    )
