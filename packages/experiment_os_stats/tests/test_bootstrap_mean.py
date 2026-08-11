"""Tests for percentile bootstrap estimation of an independent mean difference."""

import json

import numpy as np
import pytest
from scipy.stats import bootstrap

from experiment_os_stats import (
    DataValidationError,
    InsufficientSampleError,
    InvalidParameterError,
    MissingValuePolicy,
    bootstrap_mean_difference,
)

GROUP_A = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
GROUP_B = np.array([3.0, 5.0, 6.0, 7.0, 9.0, 10.0, 12.0])


def test_bootstrap_mean_returns_estimate_interval_and_metadata() -> None:
    result = bootstrap_mean_difference(
        GROUP_A,
        GROUP_B,
        n_resamples=500,
        seed=42,
    )

    assert result.statistic is None
    assert result.p_value is None
    assert result.reject_null is None
    assert result.estimate == pytest.approx(np.mean(GROUP_B) - np.mean(GROUP_A))
    assert result.confidence_interval is not None
    assert result.confidence_interval.method == "bootstrap_percentile"
    assert result.metadata["standard_error"] > 0
    assert len(result.metadata["bootstrap_distribution"]) == 500


def test_bootstrap_mean_agrees_with_scipy_percentile_reference() -> None:
    expected = bootstrap(
        (GROUP_B, GROUP_A),
        lambda group_b, group_a: np.mean(group_b) - np.mean(group_a),
        vectorized=False,
        paired=False,
        n_resamples=5_000,
        confidence_level=0.95,
        method="percentile",
        random_state=73023,
    )

    result = bootstrap_mean_difference(
        GROUP_A,
        GROUP_B,
        n_resamples=5_000,
        seed=73023,
    )

    assert result.confidence_interval is not None
    assert result.confidence_interval.lower == pytest.approx(
        expected.confidence_interval.low,
        abs=0.2,
    )
    assert result.confidence_interval.upper == pytest.approx(
        expected.confidence_interval.high,
        abs=0.2,
    )
    assert result.metadata["standard_error"] == pytest.approx(
        expected.standard_error,
        abs=0.1,
    )


def test_bootstrap_mean_respects_confidence_level() -> None:
    result = bootstrap_mean_difference(
        GROUP_A,
        GROUP_B,
        confidence_level=0.9,
        n_resamples=300,
        seed=8,
    )

    assert result.alpha == pytest.approx(0.1)
    assert result.confidence_interval is not None
    assert result.confidence_interval.level == 0.9


def test_bootstrap_mean_is_reproducible_with_fixed_seed() -> None:
    settings = {"n_resamples": 250, "seed": 99}

    first = bootstrap_mean_difference(GROUP_A, GROUP_B, **settings)
    second = bootstrap_mean_difference(GROUP_A, GROUP_B, **settings)

    assert first.metadata["standard_error"] == second.metadata["standard_error"]
    assert first.confidence_interval == second.confidence_interval
    assert first.metadata["bootstrap_distribution"] == second.metadata["bootstrap_distribution"]


def test_bootstrap_mean_changes_distribution_with_seed() -> None:
    first = bootstrap_mean_difference(GROUP_A, GROUP_B, n_resamples=150, seed=1)
    second = bootstrap_mean_difference(GROUP_A, GROUP_B, n_resamples=150, seed=2)

    assert first.metadata["bootstrap_distribution"] != second.metadata["bootstrap_distribution"]


def test_bootstrap_mean_supports_constant_groups() -> None:
    result = bootstrap_mean_difference(
        [1.0, 1.0, 1.0],
        [3.0, 3.0, 3.0],
        n_resamples=100,
        seed=7,
    )

    assert result.estimate == 2.0
    assert result.metadata["standard_error"] == 0.0
    assert result.confidence_interval is not None
    assert result.confidence_interval.lower == result.confidence_interval.upper == 2.0


def test_bootstrap_mean_drops_missing_values() -> None:
    result = bootstrap_mean_difference(
        [1.0, None, 2.0],
        [2.0, 3.0, None],
        n_resamples=100,
        seed=5,
        missing_policy=MissingValuePolicy.DROP,
    )

    assert result.metadata["n_a"] == 2
    assert result.metadata["n_b"] == 2


def test_bootstrap_mean_rejects_missing_values_when_requested() -> None:
    with pytest.raises(DataValidationError, match="missing"):
        bootstrap_mean_difference(
            [1.0, None],
            [2.0, 3.0],
            n_resamples=100,
            missing_policy=MissingValuePolicy.RAISE,
        )


@pytest.mark.parametrize("n_resamples", [99, 100_001, 100.0, True])
def test_bootstrap_mean_rejects_invalid_resample_count(n_resamples: int) -> None:
    with pytest.raises(InvalidParameterError, match="n_resamples"):
        bootstrap_mean_difference(GROUP_A, GROUP_B, n_resamples=n_resamples)


@pytest.mark.parametrize("confidence_level", [0.0, 1.0, -0.1, True, np.nan])
def test_bootstrap_mean_rejects_invalid_confidence_level(
    confidence_level: float,
) -> None:
    with pytest.raises(InvalidParameterError, match="confidence_level"):
        bootstrap_mean_difference(
            GROUP_A,
            GROUP_B,
            confidence_level=confidence_level,
            n_resamples=100,
        )


@pytest.mark.parametrize("seed", [-1, 1.5, True])
def test_bootstrap_mean_rejects_invalid_seed(seed: int) -> None:
    with pytest.raises(InvalidParameterError, match="seed"):
        bootstrap_mean_difference(GROUP_A, GROUP_B, n_resamples=100, seed=seed)


def test_bootstrap_mean_requires_two_observations_per_group() -> None:
    with pytest.raises(InsufficientSampleError):
        bootstrap_mean_difference([1.0], [2.0, 3.0], n_resamples=100)


def test_bootstrap_mean_result_is_strictly_json_compatible() -> None:
    payload = bootstrap_mean_difference(
        GROUP_A,
        GROUP_B,
        n_resamples=100,
        seed=11,
    ).to_dict()

    assert payload["confidence_interval"]["method"] == "bootstrap_percentile"
    json.dumps(payload, allow_nan=False)
