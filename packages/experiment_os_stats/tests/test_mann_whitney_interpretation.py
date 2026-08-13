"""Tests for deterministic Mann-Whitney interpretation."""

import pytest

from experiment_os_stats import StatisticalInterpretation, mann_whitney_u_test
from experiment_os_stats.interpretation import interpret_mann_whitney_result


def test_significant_mann_whitney_interpretation_describes_b_rank_advantage() -> None:
    result = mann_whitney_u_test(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [6.0, 7.0, 8.0, 9.0, 10.0],
    )
    interpretation = result.interpretation

    assert isinstance(interpretation, StatisticalInterpretation)
    assert "sufficient evidence to reject" in interpretation.decision
    assert "rank-biserial correlation is 1.000" in interpretation.effect
    assert "higher ranks in group B" in interpretation.effect
    assert "is 1.000" in interpretation.effect


def test_mann_whitney_interpretation_preserves_a_favoring_orientation() -> None:
    result = mann_whitney_u_test([4.0, 5.0, 6.0], [1.0, 2.0, 3.0])

    assert "rank-biserial correlation is -1.000" in result.interpretation.effect
    assert "higher ranks in group A" in result.interpretation.effect
    assert "is 0.000" in result.interpretation.effect


def test_non_significant_mann_whitney_interpretation_does_not_accept_null() -> None:
    result = mann_whitney_u_test([1.0, 2.0, 3.0], [1.5, 2.5, 3.5])

    assert result.reject_null is False
    assert "do not provide sufficient evidence" in result.interpretation.decision
    assert "does not establish that the null hypothesis is true" in result.interpretation.decision


def test_mann_whitney_interpretation_never_claims_to_test_medians() -> None:
    result = mann_whitney_u_test([1.0, 2.0, 4.0], [2.0, 3.0, 8.0])
    interpretation = result.interpretation

    assert "median" not in interpretation.question.lower()
    assert "median" not in interpretation.alternative_hypothesis.lower()
    assert "does not automatically test a difference in medians" in interpretation.warning_context


def test_mann_whitney_interpretation_contextualizes_ties() -> None:
    result = mann_whitney_u_test([1.0, 2.0, 2.0, 4.0], [2.0, 3.0, 3.0, 5.0])

    assert "tied values" in result.interpretation.warning_context
    assert "ties counting one half" in result.interpretation.effect


def test_mann_whitney_interpretation_states_missing_interval_and_practical_threshold() -> None:
    result = mann_whitney_u_test([1.0, 3.0, 5.0], [2.0, 4.0, 6.0])

    assert "does not include a confidence interval" in result.interpretation.uncertainty
    assert "not assessed" in result.interpretation.practical_significance


def test_zero_rank_effect_wording_is_neutral() -> None:
    interpretation = interpret_mann_whitney_result(
        rank_biserial=0.0,
        probability_of_superiority=0.5,
        p_value=1.0,
        alpha=0.05,
        warnings=(),
    )

    assert "no observed rank tendency toward either group" in interpretation.effect
    assert "is 0.500" in interpretation.effect
    assert interpretation.warning_context is None


@pytest.mark.parametrize("forbidden", ["H0 is true", "groups are identical", "median difference"])
def test_mann_whitney_interpretation_avoids_forbidden_claims(forbidden: str) -> None:
    payload = mann_whitney_u_test([1.0, 2.0, 3.0], [1.5, 2.5, 3.5]).to_dict()
    combined = " ".join(payload["interpretation"].values())

    assert forbidden.lower() not in combined.lower()
