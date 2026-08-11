"""Tests for the Monte-Carlo permutation test of independent means."""

import json

import pytest
from scipy.stats import permutation_test

from experiment_os_stats import (
    Alternative,
    DataValidationError,
    DegenerateSampleError,
    InvalidParameterError,
    MissingValuePolicy,
    permutation_mean_test,
)

GROUP_A = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
GROUP_B = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0]


def test_permutation_mean_observed_statistic_and_metadata() -> None:
    result = permutation_mean_test(GROUP_A, GROUP_B, n_permutations=200, seed=42)

    assert result.statistic == pytest.approx(3.0)
    assert result.estimate == pytest.approx(3.0)
    assert result.metadata["difference_direction"] == "group_b_minus_group_a"
    assert result.metadata["n_a"] == 6
    assert result.metadata["n_b"] == 6
    assert len(result.metadata["null_distribution"]) == 200


def test_permutation_mean_p_value_agrees_with_scipy_reference() -> None:
    expected = permutation_test(
        (GROUP_B, GROUP_A),
        lambda group_b, group_a: group_b.mean() - group_a.mean(),
        permutation_type="independent",
        alternative="two-sided",
        n_resamples=5_000,
        random_state=73022,
    )

    result = permutation_mean_test(
        GROUP_A,
        GROUP_B,
        n_permutations=5_000,
        seed=73022,
    )

    assert result.p_value == pytest.approx(expected.pvalue, abs=0.03)


@pytest.mark.parametrize(
    ("alternative", "should_reject"),
    [
        (Alternative.GREATER, True),
        (Alternative.LESS, False),
        (Alternative.TWO_SIDED, True),
    ],
)
def test_permutation_mean_supports_alternatives(
    alternative: Alternative,
    should_reject: bool,
) -> None:
    result = permutation_mean_test(
        GROUP_A,
        GROUP_B,
        alternative=alternative,
        n_permutations=2_000,
        seed=812,
    )

    assert result.reject_null is should_reject
    assert result.alternative is alternative


def test_permutation_mean_is_reproducible_with_fixed_seed() -> None:
    settings = {"n_permutations": 250, "seed": 99}

    first = permutation_mean_test(GROUP_A, GROUP_B, **settings)
    second = permutation_mean_test(GROUP_A, GROUP_B, **settings)

    assert first.p_value == second.p_value
    assert first.metadata["null_distribution"] == second.metadata["null_distribution"]


def test_permutation_mean_changes_distribution_with_seed() -> None:
    first = permutation_mean_test(GROUP_A, GROUP_B, n_permutations=150, seed=1)
    second = permutation_mean_test(GROUP_A, GROUP_B, n_permutations=150, seed=2)

    assert first.metadata["null_distribution"] != second.metadata["null_distribution"]


def test_permutation_mean_add_one_correction_prevents_zero_p_value() -> None:
    result = permutation_mean_test(
        [0.0] * 10,
        [10.0] * 10,
        alternative=Alternative.GREATER,
        n_permutations=100,
        seed=7,
    )

    assert result.p_value >= 1 / 101
    assert result.metadata["p_value_method"] == "add_one_monte_carlo"


def test_permutation_mean_drops_missing_values() -> None:
    result = permutation_mean_test(
        [1.0, None, 2.0],
        [2.0, 3.0, None],
        n_permutations=100,
        seed=5,
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 2
    assert result.metadata["n_b"] == 2


def test_permutation_mean_rejects_missing_values_when_requested() -> None:
    with pytest.raises(DataValidationError, match="missing"):
        permutation_mean_test(
            [1.0, None],
            [2.0, 3.0],
            n_permutations=100,
            missing_policy=MissingValuePolicy.RAISE,
        )


@pytest.mark.parametrize("n_permutations", [99, 100_001, 100.0, True])
def test_permutation_mean_rejects_invalid_permutation_count(
    n_permutations: int,
) -> None:
    with pytest.raises(InvalidParameterError, match="n_permutations"):
        permutation_mean_test(GROUP_A, GROUP_B, n_permutations=n_permutations)


@pytest.mark.parametrize("seed", [-1, 1.5, True])
def test_permutation_mean_rejects_invalid_seed(seed: int) -> None:
    with pytest.raises(InvalidParameterError, match="seed"):
        permutation_mean_test(GROUP_A, GROUP_B, n_permutations=100, seed=seed)


def test_permutation_mean_rejects_invalid_alternative() -> None:
    with pytest.raises(InvalidParameterError, match="alternative"):
        permutation_mean_test(
            GROUP_A,
            GROUP_B,
            alternative="up",
            n_permutations=100,
        )


def test_permutation_mean_rejects_constant_combined_data() -> None:
    with pytest.raises(DegenerateSampleError, match="variation"):
        permutation_mean_test([1.0, 1.0], [1.0, 1.0], n_permutations=100)


def test_permutation_mean_result_is_strictly_json_compatible() -> None:
    payload = permutation_mean_test(
        GROUP_A,
        GROUP_B,
        n_permutations=100,
        seed=11,
    ).to_dict()

    assert payload["confidence_interval"] is None
    json.dumps(payload, allow_nan=False)
