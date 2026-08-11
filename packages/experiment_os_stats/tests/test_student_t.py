"""Tests for Student's independent two-sample t-test."""

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
)

GROUP_A = [9.2, 10.1, 11.4, 8.8, 10.7, 9.9]
GROUP_B = [11.0, 12.3, 10.8, 13.1, 11.7, 12.0, 10.9]


@pytest.mark.parametrize(
    "alternative",
    [Alternative.TWO_SIDED, Alternative.GREATER, Alternative.LESS],
)
def test_student_t_matches_scipy(alternative: Alternative) -> None:
    expected = ttest_ind(
        GROUP_B,
        GROUP_A,
        equal_var=True,
        alternative=alternative.value,
    )

    result = student_t_test(GROUP_A, GROUP_B, alternative=alternative)

    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert result.alternative is alternative


def test_student_t_confidence_interval_matches_statsmodels() -> None:
    comparison = CompareMeans(DescrStatsW(GROUP_B), DescrStatsW(GROUP_A))
    expected_lower, expected_upper = comparison.tconfint_diff(alpha=0.05, usevar="pooled")

    result = student_t_test(GROUP_A, GROUP_B)

    assert result.confidence_interval is not None
    assert result.confidence_interval.lower == pytest.approx(expected_lower)
    assert result.confidence_interval.upper == pytest.approx(expected_upper)
    assert result.confidence_interval.method == "student_t_pooled"


def test_student_t_returns_effect_metadata_and_decision() -> None:
    result = student_t_test(GROUP_A, GROUP_B)
    pooled_standard_deviation = result.metadata["pooled_variance"] ** 0.5

    assert result.reject_null is True
    assert result.estimate == pytest.approx(result.metadata["mean_b"] - result.metadata["mean_a"])
    assert result.effect_size_name == "cohens_d"
    assert result.effect_size == pytest.approx(result.estimate / pooled_standard_deviation)
    assert result.metadata["degrees_of_freedom"] == 11
    assert result.metadata["difference_direction"] == "group_b_minus_group_a"


def test_student_t_drops_missing_values() -> None:
    result = student_t_test(
        [1.0, None, 2.0, 3.0],
        [2.0, 3.0, None, 4.0],
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 3
    assert result.metadata["n_b"] == 3


def test_student_t_rejects_missing_values_when_requested() -> None:
    with pytest.raises(DataValidationError, match="missing"):
        student_t_test(
            [1.0, None, 2.0],
            [2.0, 3.0, 4.0],
            missing_policy=MissingValuePolicy.RAISE,
        )


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1])
def test_student_t_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(InvalidParameterError, match="alpha"):
        student_t_test(GROUP_A, GROUP_B, alpha=alpha)


def test_student_t_rejects_invalid_alternative() -> None:
    with pytest.raises(InvalidParameterError, match="alternative"):
        student_t_test(GROUP_A, GROUP_B, alternative="up")


def test_student_t_requires_two_observations_per_group() -> None:
    with pytest.raises(InsufficientSampleError):
        student_t_test([1.0], [2.0, 3.0])


def test_student_t_rejects_zero_pooled_variance() -> None:
    with pytest.raises(DegenerateSampleError, match="pooled variance"):
        student_t_test([1.0, 1.0], [2.0, 2.0])
