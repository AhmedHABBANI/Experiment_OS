"""Tests for Fisher's exact test on independent binary samples."""

import json

import numpy as np
import pytest
from scipy.stats import fisher_exact

from experiment_os_stats import (
    Alternative,
    DataValidationError,
    DegenerateSampleError,
    InvalidParameterError,
    MissingValuePolicy,
    fisher_exact_test,
)


def _binary_sample(successes: int, n: int) -> np.ndarray:
    return np.array([1] * successes + [0] * (n - successes), dtype=int)


@pytest.mark.parametrize(
    "alternative",
    [Alternative.TWO_SIDED, Alternative.GREATER, Alternative.LESS],
)
def test_fisher_exact_matches_scipy(alternative: Alternative) -> None:
    group_a = _binary_sample(4, 20)
    group_b = _binary_sample(11, 22)
    expected = fisher_exact(
        [[11, 11], [4, 16]],
        alternative=alternative.value,
    )

    result = fisher_exact_test(group_a, group_b, alternative=alternative)

    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert result.effect_size == pytest.approx(expected.statistic)
    assert result.alternative is alternative


def test_fisher_exact_returns_stable_metadata_and_decision() -> None:
    result = fisher_exact_test(_binary_sample(2, 20), _binary_sample(12, 20))

    assert result.reject_null is True
    assert result.estimate == pytest.approx(0.5)
    assert result.metadata["contingency_table"] == [[12, 8], [2, 18]]
    assert result.metadata["contingency_table_rows"] == ["group_b", "group_a"]
    assert result.metadata["risk_ratio"] == pytest.approx(6.0)
    assert result.interpretation["null_hypothesis"].endswith("independent.")


def test_fisher_exact_preserves_zero_odds_ratio() -> None:
    result = fisher_exact_test(_binary_sample(2, 10), _binary_sample(0, 10))

    assert result.statistic == 0.0
    assert result.effect_size == 0.0
    assert result.effect_size_name == "odds_ratio"
    assert result.warnings == ()


def test_fisher_exact_replaces_infinite_odds_ratio_with_warning() -> None:
    result = fisher_exact_test(_binary_sample(0, 10), _binary_sample(3, 10))
    payload = result.to_dict()

    assert result.statistic is None
    assert result.effect_size is None
    assert result.metadata["odds_ratio"] is None
    assert result.warnings[0].code == "NON_FINITE_ODDS_RATIO"
    assert "Infinity" not in json.dumps(payload)


@pytest.mark.parametrize("constant", [0, 1])
def test_fisher_exact_rejects_degenerate_combined_outcome(constant: int) -> None:
    with pytest.raises(DegenerateSampleError, match="both outcomes"):
        fisher_exact_test([constant] * 8, [constant] * 9)


def test_fisher_exact_drops_missing_values() -> None:
    result = fisher_exact_test(
        [1, 0, None, 0],
        [1, 1, 0, None],
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 3
    assert result.metadata["n_b"] == 3


def test_fisher_exact_rejects_invalid_binary_data() -> None:
    with pytest.raises(DataValidationError):
        fisher_exact_test([0, 2], [0, 1])


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1])
def test_fisher_exact_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(InvalidParameterError, match="alpha"):
        fisher_exact_test([0, 1], [0, 1], alpha=alpha)


def test_fisher_exact_rejects_invalid_alternative() -> None:
    with pytest.raises(InvalidParameterError, match="alternative"):
        fisher_exact_test([0, 1], [0, 1], alternative="up")
