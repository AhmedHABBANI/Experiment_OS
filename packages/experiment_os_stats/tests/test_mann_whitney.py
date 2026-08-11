"""Tests for the independent two-sided Mann-Whitney U test."""

import json

import pytest
from scipy.stats import mannwhitneyu

from experiment_os_stats import (
    DataValidationError,
    DegenerateSampleError,
    InvalidParameterError,
    MissingValuePolicy,
    mann_whitney_u_test,
)


def test_mann_whitney_matches_scipy_without_ties() -> None:
    group_a = [1.0, 3.0, 5.0, 7.0, 9.0]
    group_b = [2.0, 6.0, 8.0, 10.0]
    expected = mannwhitneyu(group_b, group_a, alternative="two-sided", method="auto")

    result = mann_whitney_u_test(group_a, group_b)

    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert result.metadata["u_statistic_group"] == "group_b"
    assert result.metadata["ties_present"] is False


def test_mann_whitney_matches_scipy_with_ties() -> None:
    group_a = [1.0, 2.0, 2.0, 4.0]
    group_b = [2.0, 3.0, 3.0, 5.0]
    expected = mannwhitneyu(group_b, group_a, alternative="two-sided", method="auto")

    result = mann_whitney_u_test(group_a, group_b)

    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert any(warning.code == "TIES_PRESENT" for warning in result.warnings)


def test_mann_whitney_rank_biserial_is_oriented_b_over_a() -> None:
    result = mann_whitney_u_test(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [6.0, 7.0, 8.0, 9.0, 10.0],
    )

    assert result.statistic == 25.0
    assert result.effect_size == 1.0
    assert result.effect_size_name == "rank_biserial_correlation"
    assert result.metadata["probability_of_superiority_b_over_a"] == 1.0
    assert result.reject_null is True


def test_mann_whitney_rank_biserial_reverses_with_groups() -> None:
    result = mann_whitney_u_test([4.0, 5.0, 6.0], [1.0, 2.0, 3.0])

    assert result.effect_size == -1.0
    assert result.metadata["probability_of_superiority_b_over_a"] == 0.0


def test_mann_whitney_warns_against_automatic_median_interpretation() -> None:
    result = mann_whitney_u_test([1.0, 2.0, 4.0], [2.0, 3.0, 8.0])
    warning = result.warnings[0]

    assert warning.code == "MANN_WHITNEY_NOT_MEDIAN_TEST"
    assert "medians" in warning.message
    assert "median" not in result.interpretation["alternative_hypothesis"]


def test_mann_whitney_drops_missing_values() -> None:
    result = mann_whitney_u_test(
        [1.0, None, 2.0],
        [2.0, 3.0, None],
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 2
    assert result.metadata["n_b"] == 2


def test_mann_whitney_rejects_missing_values_when_requested() -> None:
    with pytest.raises(DataValidationError, match="missing"):
        mann_whitney_u_test(
            [1.0, None],
            [2.0, 3.0],
            missing_policy=MissingValuePolicy.RAISE,
        )


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1])
def test_mann_whitney_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(InvalidParameterError, match="alpha"):
        mann_whitney_u_test([1.0, 2.0], [3.0, 4.0], alpha=alpha)


def test_mann_whitney_rejects_identical_combined_observations() -> None:
    with pytest.raises(DegenerateSampleError, match="distinct combined"):
        mann_whitney_u_test([1.0, 1.0], [1.0, 1.0])


def test_mann_whitney_result_is_strictly_json_compatible() -> None:
    payload = mann_whitney_u_test([1.0, 2.0], [3.0, 4.0]).to_dict()

    assert payload["confidence_interval"] is None
    json.dumps(payload, allow_nan=False)
