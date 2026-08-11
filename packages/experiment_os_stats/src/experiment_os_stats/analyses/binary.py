"""Frequentist analyses for independent binary A/B samples."""

from math import isfinite, sqrt

import numpy as np
from scipy.stats import fisher_exact as scipy_fisher_exact
from scipy.stats import norm

from experiment_os_stats.analyses._common import normalize_alternative, validate_alpha
from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples
from experiment_os_stats.exceptions import DegenerateSampleError
from experiment_os_stats.results import ConfidenceInterval, StatisticalResult, StatisticalWarning
from experiment_os_stats.types import Alternative, MetricType, MissingValuePolicy, WarningSeverity


def _p_value(statistic: float, alternative: Alternative) -> float:
    """Compute a normal-reference p-value for the selected alternative."""
    if alternative is Alternative.GREATER:
        return float(norm.sf(statistic))
    if alternative is Alternative.LESS:
        return float(norm.cdf(statistic))
    return float(2 * norm.sf(abs(statistic)))


def _odds_ratio(
    successes_a: int, failures_a: int, successes_b: int, failures_b: int
) -> float | None:
    """Return the B-to-A sample odds ratio when finite and defined."""
    if min(successes_a, failures_a, successes_b, failures_b) == 0:
        return None
    return (successes_b * failures_a) / (failures_b * successes_a)


def _risk_ratio(proportion_a: float, proportion_b: float) -> float | None:
    """Return the B-to-A risk ratio when the A risk is non-zero."""
    if proportion_a == 0:
        return None
    return proportion_b / proportion_a


def _asymptotic_warnings(
    *,
    n_a: int,
    n_b: int,
    pooled_proportion: float,
) -> tuple[StatisticalWarning, ...]:
    """Warn when null-model expected counts weaken the normal approximation."""
    expected_counts = (
        n_a * pooled_proportion,
        n_a * (1 - pooled_proportion),
        n_b * pooled_proportion,
        n_b * (1 - pooled_proportion),
    )
    minimum_expected_count = min(expected_counts)
    if minimum_expected_count >= 5:
        return ()

    return (
        StatisticalWarning(
            code="SMALL_EXPECTED_COUNT",
            message=(
                "At least one expected count under the null hypothesis is below five; "
                "the normal approximation may be inaccurate."
            ),
            severity=WarningSeverity.WARNING,
            details={
                "minimum_expected_count": float(minimum_expected_count),
                "recommended_minimum": 5,
            },
        ),
    )


def two_proportion_z_test(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    alpha: float = 0.05,
    alternative: Alternative | str = Alternative.TWO_SIDED,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Test equality of two independent proportions, with effects oriented B minus A.

    The null test uses the pooled standard error. The confidence interval uses the
    unpooled Wald standard error and always reports a two-sided ``1 - alpha`` interval.
    """
    validate_alpha(alpha)
    normalized_alternative = normalize_alternative(alternative)
    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.BINARY,
        missing_policy=missing_policy,
        minimum_size=1,
    )

    n_a = int(validated.group_a.values.size)
    n_b = int(validated.group_b.values.size)
    successes_a = int(np.sum(validated.group_a.values))
    successes_b = int(np.sum(validated.group_b.values))
    failures_a = n_a - successes_a
    failures_b = n_b - successes_b
    proportion_a = successes_a / n_a
    proportion_b = successes_b / n_b
    difference = proportion_b - proportion_a
    pooled_proportion = (successes_a + successes_b) / (n_a + n_b)
    pooled_standard_error = sqrt(pooled_proportion * (1 - pooled_proportion) * (1 / n_a + 1 / n_b))

    if pooled_standard_error == 0:
        raise DegenerateSampleError(
            "The pooled standard error is zero, so the z statistic is undefined.",
            details={
                "successes_a": successes_a,
                "successes_b": successes_b,
                "n_a": n_a,
                "n_b": n_b,
            },
        )

    statistic = difference / pooled_standard_error
    unpooled_standard_error = sqrt(
        proportion_a * (1 - proportion_a) / n_a + proportion_b * (1 - proportion_b) / n_b
    )
    critical_value = float(norm.ppf(1 - alpha / 2))
    confidence_interval = ConfidenceInterval(
        lower=difference - critical_value * unpooled_standard_error,
        upper=difference + critical_value * unpooled_standard_error,
        level=1 - alpha,
        parameter="difference_in_proportions_b_minus_a",
        method="wald_unpooled",
    )
    odds_ratio = _odds_ratio(successes_a, failures_a, successes_b, failures_b)

    return StatisticalResult(
        test_name="two_proportion_z_test",
        metric_type=MetricType.BINARY,
        statistic=float(statistic),
        p_value=_p_value(statistic, normalized_alternative),
        alpha=alpha,
        alternative=normalized_alternative,
        estimate=float(difference),
        confidence_interval=confidence_interval,
        effect_size=odds_ratio,
        effect_size_name="odds_ratio" if odds_ratio is not None else None,
        assumptions=(
            "The two groups contain independent observations.",
            "Each observation has a binary outcome.",
            "The pooled normal approximation is sufficiently accurate for the null test.",
        ),
        warnings=_asymptotic_warnings(
            n_a=n_a,
            n_b=n_b,
            pooled_proportion=pooled_proportion,
        ),
        interpretation={
            "null_hypothesis": "The population proportions in groups A and B are equal.",
            "alternative_hypothesis": (
                "The population proportion in group B differs from group A."
                if normalized_alternative is Alternative.TWO_SIDED
                else (
                    "The population proportion in group B is "
                    f"{normalized_alternative.value} than group A."
                )
            ),
        },
        metadata={
            "n_a": n_a,
            "n_b": n_b,
            "successes_a": successes_a,
            "successes_b": successes_b,
            "failures_a": failures_a,
            "failures_b": failures_b,
            "proportion_a": proportion_a,
            "proportion_b": proportion_b,
            "pooled_proportion": pooled_proportion,
            "risk_ratio": _risk_ratio(proportion_a, proportion_b),
            "odds_ratio": odds_ratio,
            "difference_direction": "group_b_minus_group_a",
        },
    )


def fisher_exact_test(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    alpha: float = 0.05,
    alternative: Alternative | str = Alternative.TWO_SIDED,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> StatisticalResult:
    """Run Fisher's exact test on independent binary A/B samples.

    The contingency table places group B first, so the sample odds ratio and
    directional alternatives consistently compare group B with group A.
    """
    validate_alpha(alpha)
    normalized_alternative = normalize_alternative(alternative)
    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.BINARY,
        missing_policy=missing_policy,
        minimum_size=1,
    )

    n_a = int(validated.group_a.values.size)
    n_b = int(validated.group_b.values.size)
    successes_a = int(np.sum(validated.group_a.values))
    successes_b = int(np.sum(validated.group_b.values))
    failures_a = n_a - successes_a
    failures_b = n_b - successes_b
    total_successes = successes_a + successes_b
    total_failures = failures_a + failures_b

    if total_successes == 0 or total_failures == 0:
        raise DegenerateSampleError(
            "Fisher's exact test requires both outcomes to occur in the combined data.",
            details={
                "total_successes": total_successes,
                "total_failures": total_failures,
            },
        )

    contingency_table = [
        [successes_b, failures_b],
        [successes_a, failures_a],
    ]
    reference = scipy_fisher_exact(
        contingency_table,
        alternative=normalized_alternative.value,
    )
    raw_odds_ratio = float(reference.statistic)
    odds_ratio = raw_odds_ratio if isfinite(raw_odds_ratio) else None
    warnings = (
        (
            StatisticalWarning(
                code="NON_FINITE_ODDS_RATIO",
                message=(
                    "The sample odds ratio is not finite because the contingency table "
                    "contains a zero cell."
                ),
                severity=WarningSeverity.WARNING,
                details={"contingency_table": contingency_table},
            ),
        )
        if odds_ratio is None
        else ()
    )
    proportion_a = successes_a / n_a
    proportion_b = successes_b / n_b

    return StatisticalResult(
        test_name="fisher_exact_test",
        metric_type=MetricType.BINARY,
        statistic=odds_ratio,
        p_value=float(reference.pvalue),
        alpha=alpha,
        alternative=normalized_alternative,
        estimate=proportion_b - proportion_a,
        effect_size=odds_ratio,
        effect_size_name="odds_ratio" if odds_ratio is not None else None,
        assumptions=(
            "The two groups contain independent observations.",
            "Each observation has a binary outcome.",
            "Group totals and the combined outcome totals are treated as fixed.",
        ),
        warnings=warnings,
        interpretation={
            "null_hypothesis": "The outcome and group membership are independent.",
            "alternative_hypothesis": (
                "The outcome and group membership are associated."
                if normalized_alternative is Alternative.TWO_SIDED
                else (
                    "The odds of success in group B are "
                    f"{normalized_alternative.value} than in group A."
                )
            ),
        },
        metadata={
            "n_a": n_a,
            "n_b": n_b,
            "successes_a": successes_a,
            "successes_b": successes_b,
            "failures_a": failures_a,
            "failures_b": failures_b,
            "proportion_a": proportion_a,
            "proportion_b": proportion_b,
            "contingency_table": contingency_table,
            "contingency_table_rows": ["group_b", "group_a"],
            "contingency_table_columns": ["success", "failure"],
            "odds_ratio": odds_ratio,
            "risk_ratio": _risk_ratio(proportion_a, proportion_b),
            "difference_direction": "group_b_minus_group_a",
        },
    )
