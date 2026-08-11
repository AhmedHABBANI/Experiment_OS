"""Tests for the independent two-proportion z-test."""

from math import isclose

import numpy as np
import pytest
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

from experiment_os_stats import (
    Alternative,
    DataValidationError,
    DegenerateSampleError,
    InvalidParameterError,
    MissingValuePolicy,
    two_proportion_z_test,
)


def _binary_sample(successes: int, n: int) -> np.ndarray:
    return np.array([1] * successes + [0] * (n - successes), dtype=int)


@pytest.mark.parametrize(
    "alternative",
    [Alternative.TWO_SIDED, Alternative.GREATER, Alternative.LESS],
)
def test_two_proportion_z_matches_statsmodels(alternative: Alternative) -> None:
    group_a = _binary_sample(42, 120)
    group_b = _binary_sample(61, 130)

    result = two_proportion_z_test(group_a, group_b, alternative=alternative)
    statsmodels_alternative = {
        Alternative.TWO_SIDED: "two-sided",
        Alternative.GREATER: "larger",
        Alternative.LESS: "smaller",
    }[alternative]
    expected_statistic, expected_p_value = proportions_ztest(
        count=[61, 42],
        nobs=[130, 120],
        alternative=statsmodels_alternative,
    )

    assert result.statistic == pytest.approx(expected_statistic)
    assert result.p_value == pytest.approx(expected_p_value)
    assert result.estimate == pytest.approx((61 / 130) - (42 / 120))
    assert result.alternative is alternative


def test_two_proportion_z_confidence_interval_matches_statsmodels_wald() -> None:
    result = two_proportion_z_test(_binary_sample(42, 120), _binary_sample(61, 130))
    expected_lower, expected_upper = confint_proportions_2indep(
        count1=61,
        nobs1=130,
        count2=42,
        nobs2=120,
        method="wald",
        compare="diff",
        alpha=0.05,
    )

    assert result.confidence_interval is not None
    assert result.confidence_interval.lower == pytest.approx(expected_lower)
    assert result.confidence_interval.upper == pytest.approx(expected_upper)
    assert result.confidence_interval.level == 0.95
    assert result.confidence_interval.method == "wald_unpooled"


def test_two_proportion_z_returns_effects_metadata_and_decision() -> None:
    result = two_proportion_z_test(_binary_sample(20, 100), _binary_sample(40, 100))

    assert result.reject_null is True
    assert result.effect_size_name == "odds_ratio"
    assert result.effect_size == pytest.approx((40 * 80) / (60 * 20))
    assert result.metadata["risk_ratio"] == pytest.approx(2.0)
    assert result.metadata["difference_direction"] == "group_b_minus_group_a"
    assert result.interpretation["null_hypothesis"].startswith("The population proportions")


def test_two_proportion_z_warns_for_small_expected_counts() -> None:
    result = two_proportion_z_test(_binary_sample(0, 8), _binary_sample(2, 8))

    assert len(result.warnings) == 1
    assert result.warnings[0].code == "SMALL_EXPECTED_COUNT"
    assert result.warnings[0].details["minimum_expected_count"] == pytest.approx(1.0)


def test_two_proportion_z_drops_missing_values() -> None:
    result = two_proportion_z_test(
        [1, 0, 1, None],
        [1, 1, 0, 0],
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 3
    assert result.metadata["n_b"] == 4


def test_two_proportion_z_rejects_invalid_binary_data() -> None:
    with pytest.raises(DataValidationError):
        two_proportion_z_test([0, 2], [0, 1])


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1])
def test_two_proportion_z_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(InvalidParameterError, match="alpha"):
        two_proportion_z_test([0, 1], [0, 1], alpha=alpha)


def test_two_proportion_z_rejects_invalid_alternative() -> None:
    with pytest.raises(InvalidParameterError, match="alternative"):
        two_proportion_z_test([0, 1], [0, 1], alternative="up")


@pytest.mark.parametrize("constant", [0, 1])
def test_two_proportion_z_rejects_zero_pooled_variance(constant: int) -> None:
    with pytest.raises(DegenerateSampleError, match="pooled standard error"):
        two_proportion_z_test([constant] * 10, [constant] * 10)


def test_two_proportion_z_boundary_effects_are_not_forced() -> None:
    result = two_proportion_z_test(_binary_sample(2, 10), _binary_sample(10, 10))

    assert result.effect_size is None
    assert result.effect_size_name is None
    assert result.metadata["odds_ratio"] is None
    assert isclose(result.metadata["risk_ratio"], 5.0)
