"""Tests for deterministic permutation-test interpretation."""

import pytest

from experiment_os_stats import Alternative, StatisticalInterpretation, permutation_mean_test
from experiment_os_stats.interpretation import interpret_permutation_mean_result


def test_significant_permutation_interpretation_describes_effect_and_reproducibility() -> None:
    result = permutation_mean_test(
        [1, 2, 3, 4, 5, 6],
        [4, 5, 6, 7, 8, 9],
        n_permutations=2_000,
        seed=812,
    )

    assert isinstance(result.interpretation, StatisticalInterpretation)
    assert "sufficient evidence to reject" in result.interpretation.decision
    assert "3 units higher" in result.interpretation.effect
    assert "2000 random permutations" in result.interpretation.uncertainty
    assert "Seed 812" in result.interpretation.uncertainty
    assert "add-one correction" in result.interpretation.uncertainty


def test_non_significant_permutation_interpretation_does_not_accept_null() -> None:
    result = permutation_mean_test(
        [1, 2, 3, 4],
        [1.1, 2.1, 3.1, 4.1],
        n_permutations=500,
        seed=4,
    )

    assert result.reject_null is False
    assert "do not provide sufficient evidence" in result.interpretation.decision
    assert "does not establish that the null hypothesis is true" in result.interpretation.decision


@pytest.mark.parametrize(
    ("alternative", "expected"),
    [(Alternative.GREATER, "greater than"), (Alternative.LESS, "less than")],
)
def test_permutation_interpretation_matches_directional_alternative(
    alternative: Alternative,
    expected: str,
) -> None:
    result = permutation_mean_test(
        [1, 2, 3],
        [2, 3, 4],
        alternative=alternative,
        n_permutations=100,
        seed=3,
    )

    assert expected in result.interpretation.alternative_hypothesis


def test_permutation_interpretation_discloses_unseeded_non_reproducibility() -> None:
    result = permutation_mean_test([1, 2, 3], [2, 3, 4], n_permutations=100)

    assert "No seed was provided" in result.interpretation.uncertainty
    assert "not guaranteed" in result.interpretation.uncertainty


def test_permutation_resolution_matches_add_one_denominator() -> None:
    interpretation = interpret_permutation_mean_result(
        estimate=-2.0,
        p_value=0.5,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
        n_permutations=999,
        seed=1,
    )

    assert "2 units lower" in interpretation.effect
    assert "resolution of 0.001" in interpretation.uncertainty
    assert "not a confidence interval" in interpretation.uncertainty


def test_zero_permutation_effect_wording_is_neutral() -> None:
    interpretation = interpret_permutation_mean_result(
        estimate=0.0,
        p_value=1.0,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
        n_permutations=100,
        seed=1,
    )

    assert "difference of 0 units" in interpretation.effect
    assert "not assessed" in interpretation.practical_significance
