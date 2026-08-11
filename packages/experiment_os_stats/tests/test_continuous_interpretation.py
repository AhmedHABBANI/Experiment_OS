"""Tests for deterministic interpretation of Student and Welch analyses."""

import pytest

from experiment_os_stats import Alternative, StatisticalInterpretation, student_t_test, welch_t_test
from experiment_os_stats.interpretation import interpret_continuous_parametric_result
from experiment_os_stats.results import ConfidenceInterval


def test_significant_student_interpretation_describes_mean_difference_and_interval() -> None:
    result = student_t_test([1, 2, 3, 4, 5], [5, 6, 7, 8, 9])
    interpretation = result.interpretation

    assert isinstance(interpretation, StatisticalInterpretation)
    assert "sufficient evidence to reject" in interpretation.decision
    assert "4 units higher" in interpretation.effect
    assert f"Cohen's d = {result.effect_size:.3f}" in interpretation.effect
    assert "lies above zero" in interpretation.uncertainty
    assert "not assessed" in interpretation.practical_significance


def test_non_significant_welch_interpretation_does_not_accept_the_null() -> None:
    result = welch_t_test([1, 2, 3, 4, 5], [1.2, 2.2, 3.2, 4.2, 5.2])
    interpretation = result.interpretation

    assert result.reject_null is False
    assert "do not provide sufficient evidence" in interpretation.decision
    assert "does not establish that the null hypothesis is true" in interpretation.decision
    assert "includes zero" in interpretation.uncertainty


def test_continuous_interpretation_preserves_negative_b_minus_a_orientation() -> None:
    result = student_t_test([5, 6, 7, 8, 9], [1, 2, 3, 4, 5])

    assert result.estimate == pytest.approx(-4)
    assert "4 units lower" in result.interpretation.effect
    assert "lies below zero" in result.interpretation.uncertainty


@pytest.mark.parametrize(
    ("alternative", "expected"),
    [(Alternative.GREATER, "greater than"), (Alternative.LESS, "less than")],
)
def test_continuous_directional_hypothesis_matches_selected_alternative(
    alternative: Alternative,
    expected: str,
) -> None:
    result = welch_t_test(
        [1, 2, 3, 4, 5],
        [2, 3, 4, 5, 6],
        alternative=alternative,
    )

    assert expected in result.interpretation.alternative_hypothesis


def test_continuous_interpretation_reports_cohens_d_without_magnitude_label() -> None:
    interpretation = interpret_continuous_parametric_result(
        estimate=2.0,
        cohens_d=0.8,
        p_value=0.01,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
        confidence_interval=ConfidenceInterval(0.5, 3.5),
    )

    assert "Cohen's d = 0.800" in interpretation.effect
    assert not {"small", "medium", "large"}.intersection(interpretation.effect.lower().split())


@pytest.mark.parametrize("test", [student_t_test, welch_t_test])
def test_continuous_interpretation_contextualizes_imbalance_and_outliers(test) -> None:
    result = test(
        [0.0, 10.0],
        [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 8.0],
    )

    assert result.interpretation.warning_context is not None
    assert "strongly imbalanced" in result.interpretation.warning_context
    assert "mean-based inference may be sensitive" in result.interpretation.warning_context


def test_zero_mean_difference_wording_remains_descriptive() -> None:
    interpretation = interpret_continuous_parametric_result(
        estimate=0.0,
        cohens_d=0.0,
        p_value=1.0,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
        confidence_interval=ConfidenceInterval(-1.0, 1.0),
    )

    assert interpretation.effect == (
        "The observed group means are equal; the standardized difference is Cohen's d = 0.000."
    )
