"""Tests for Welch's independent two-sample t-test."""

import numpy as np
import pytest
from scipy.stats import ttest_ind
from statsmodels.stats.weightstats import CompareMeans, DescrStatsW

from experiment_os_stats import (
    Alternative,
    DataValidationError,
    DegenerateSampleError,
    InsufficientSampleError,
    InvalidParameterError,
    MissingValuePolicy,
    student_t_test,
    welch_t_test,
)

GROUP_A = [9.7, 10.2, 10.5, 9.9, 10.1, 9.8]
GROUP_B = [7.2, 9.1, 10.8, 12.6, 14.4, 16.1, 8.5, 13.7]


@pytest.mark.parametrize(
    "alternative",
    [Alternative.TWO_SIDED, Alternative.GREATER, Alternative.LESS],
)
def test_welch_t_matches_scipy(alternative: Alternative) -> None:
    expected = ttest_ind(
        GROUP_B,
        GROUP_A,
        equal_var=False,
        alternative=alternative.value,
    )

    result = welch_t_test(GROUP_A, GROUP_B, alternative=alternative)

    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert result.alternative is alternative


def test_welch_t_confidence_interval_matches_statsmodels() -> None:
    comparison = CompareMeans(DescrStatsW(GROUP_B), DescrStatsW(GROUP_A))
    expected_lower, expected_upper = comparison.tconfint_diff(alpha=0.05, usevar="unequal")

    result = welch_t_test(GROUP_A, GROUP_B)

    assert result.confidence_interval is not None
    assert result.confidence_interval.lower == pytest.approx(expected_lower)
    assert result.confidence_interval.upper == pytest.approx(expected_upper)
    assert result.confidence_interval.method == "welch_t"


def test_welch_t_returns_effect_metadata_and_decision() -> None:
    result = welch_t_test(GROUP_A, GROUP_B)
    pooled_standard_deviation = result.metadata["pooled_variance_for_effect_size"] ** 0.5
    variance_term_a = np.var(GROUP_A, ddof=1) / len(GROUP_A)
    variance_term_b = np.var(GROUP_B, ddof=1) / len(GROUP_B)
    expected_degrees_of_freedom = (variance_term_a + variance_term_b) ** 2 / (
        variance_term_a**2 / (len(GROUP_A) - 1) + variance_term_b**2 / (len(GROUP_B) - 1)
    )

    assert result.reject_null is False
    assert result.estimate == pytest.approx(result.metadata["mean_b"] - result.metadata["mean_a"])
    assert result.effect_size_name == "cohens_d"
    assert result.effect_size == pytest.approx(result.estimate / pooled_standard_deviation)
    assert result.metadata["degrees_of_freedom"] == pytest.approx(expected_degrees_of_freedom)
    assert result.metadata["degrees_of_freedom_method"] == "welch_satterthwaite"
    assert result.metadata["difference_direction"] == "group_b_minus_group_a"


def test_welch_t_matches_student_when_sample_variances_and_sizes_match() -> None:
    group_a = [1.0, 2.0, 3.0, 4.0]
    group_b = [3.0, 4.0, 5.0, 6.0]

    welch_result = welch_t_test(group_a, group_b)
    student_result = student_t_test(group_a, group_b)

    assert welch_result.statistic == pytest.approx(student_result.statistic)
    assert welch_result.p_value == pytest.approx(student_result.p_value)
    assert welch_result.metadata["degrees_of_freedom"] == pytest.approx(
        student_result.metadata["degrees_of_freedom"]
    )


def test_welch_t_accepts_one_constant_group() -> None:
    result = welch_t_test([1.0, 1.0, 1.0], [1.0, 2.0, 4.0, 8.0])

    assert result.metadata["variance_a"] == 0.0
    assert result.metadata["degrees_of_freedom"] == pytest.approx(3.0)


def test_welch_t_drops_missing_values() -> None:
    result = welch_t_test(
        [1.0, None, 2.0, 3.0],
        [2.0, 3.0, None, 5.0],
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 3
    assert result.metadata["n_b"] == 3


def test_welch_t_rejects_missing_values_when_requested() -> None:
    with pytest.raises(DataValidationError, match="missing"):
        welch_t_test(
            [1.0, None, 2.0],
            [2.0, 3.0, 4.0],
            missing_policy=MissingValuePolicy.RAISE,
        )


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1])
def test_welch_t_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(InvalidParameterError, match="alpha"):
        welch_t_test(GROUP_A, GROUP_B, alpha=alpha)


def test_welch_t_rejects_invalid_alternative() -> None:
    with pytest.raises(InvalidParameterError, match="alternative"):
        welch_t_test(GROUP_A, GROUP_B, alternative="up")


def test_welch_t_requires_two_observations_per_group() -> None:
    with pytest.raises(InsufficientSampleError):
        welch_t_test([1.0], [2.0, 3.0])


def test_welch_t_rejects_zero_standard_error() -> None:
    with pytest.raises(DegenerateSampleError, match="standard error"):
        welch_t_test([1.0, 1.0], [2.0, 2.0])
