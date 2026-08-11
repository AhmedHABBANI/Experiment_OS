"""Tests for deterministic interpretation of binary A/B analyses."""

import json

import numpy as np
import pytest

from experiment_os_stats import (
    Alternative,
    ConfidenceInterval,
    StatisticalInterpretation,
    fisher_exact_test,
    two_proportion_z_test,
)
from experiment_os_stats.interpretation import interpret_binary_result


def _binary_sample(successes: int, n: int) -> np.ndarray:
    return np.array([1] * successes + [0] * (n - successes), dtype=int)


def test_significant_z_interpretation_describes_decision_effect_and_interval() -> None:
    result = two_proportion_z_test(_binary_sample(20, 100), _binary_sample(40, 100))
    interpretation = result.interpretation

    assert isinstance(interpretation, StatisticalInterpretation)
    assert "sufficient evidence to reject" in interpretation.decision
    assert "20.00 percentage points higher" in interpretation.effect
    assert "lies above zero" in interpretation.uncertainty
    assert "not assessed" in interpretation.practical_significance


def test_non_significant_z_interpretation_does_not_accept_the_null() -> None:
    result = two_proportion_z_test(_binary_sample(48, 100), _binary_sample(52, 100))
    interpretation = result.interpretation

    assert result.reject_null is False
    assert "do not provide sufficient evidence" in interpretation.decision
    assert "does not establish that the null hypothesis is true" in interpretation.decision
    assert "includes zero" in interpretation.uncertainty


@pytest.mark.parametrize(
    ("estimate", "expected_direction"),
    [(0.125, "higher"), (-0.125, "lower"), (0.0, "equal")],
)
def test_binary_effect_wording_respects_b_minus_a_orientation(
    estimate: float,
    expected_direction: str,
) -> None:
    interpretation = interpret_binary_result(
        test_name="two_proportion_z_test",
        estimate=estimate,
        p_value=0.5,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
        confidence_interval=ConfidenceInterval(-0.2, 0.2),
    )

    assert expected_direction in interpretation.effect


@pytest.mark.parametrize(
    ("alternative", "expected"),
    [(Alternative.GREATER, "greater than"), (Alternative.LESS, "less than")],
)
def test_directional_fisher_interpretation_matches_selected_alternative(
    alternative: Alternative,
    expected: str,
) -> None:
    result = fisher_exact_test(
        _binary_sample(4, 20),
        _binary_sample(11, 22),
        alternative=alternative,
    )

    assert expected in result.interpretation.alternative_hypothesis
    assert "does not include a confidence interval" in result.interpretation.uncertainty


def test_binary_interpretation_contextualizes_statistical_warnings() -> None:
    result = two_proportion_z_test(_binary_sample(0, 8), _binary_sample(2, 8))

    assert result.interpretation.warning_context is not None
    assert "normal approximation may be inaccurate" in result.interpretation.warning_context


def test_structured_interpretation_serializes_without_null_fields() -> None:
    interpretation = StatisticalInterpretation(
        null_hypothesis="The rates are equal.",
        alternative_hypothesis="The rates differ.",
    )

    assert interpretation.to_dict() == {
        "null_hypothesis": "The rates are equal.",
        "alternative_hypothesis": "The rates differ.",
    }
    assert (
        json.loads(json.dumps(interpretation.to_dict()))["null_hypothesis"]
        == "The rates are equal."
    )


def test_structured_interpretation_rejects_blank_messages() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        StatisticalInterpretation(
            null_hypothesis="The rates are equal.",
            alternative_hypothesis="The rates differ.",
            decision=" ",
        )
