"""Tests for continuous A/B simulation."""

import math

import numpy as np
import pytest

from experiment_os_stats import (
    ContinuousDistribution,
    InvalidParameterError,
    MetricType,
    simulate_continuous_ab,
)


def test_continuous_simulation_is_reproducible_with_seed() -> None:
    first = simulate_continuous_ab(
        n_a=20,
        n_b=30,
        mean_a=10.0,
        mean_b=12.0,
        std_a=2.0,
        std_b=3.0,
        seed=123,
        missing_rate=0.1,
        outlier_rate=0.1,
    )
    second = simulate_continuous_ab(
        n_a=20,
        n_b=30,
        mean_a=10.0,
        mean_b=12.0,
        std_a=2.0,
        std_b=3.0,
        seed=123,
        missing_rate=0.1,
        outlier_rate=0.1,
    )

    np.testing.assert_array_equal(first.group_a, second.group_a)
    np.testing.assert_array_equal(first.group_b, second.group_b)
    assert first.metadata == second.metadata


def test_continuous_simulation_preserves_requested_group_sizes() -> None:
    result = simulate_continuous_ab(
        n_a=11,
        n_b=17,
        mean_a=1.0,
        mean_b=2.0,
        std_a=1.5,
        std_b=2.5,
        seed=42,
    )

    assert result.group_a.shape == (11,)
    assert result.group_b.shape == (17,)
    assert result.metadata["n_a"] == 11
    assert result.metadata["n_b"] == 17


def test_normal_simulation_matches_numpy_reference_for_seeded_draws() -> None:
    result = simulate_continuous_ab(
        n_a=4,
        n_b=3,
        mean_a=10.0,
        mean_b=20.0,
        std_a=2.0,
        std_b=5.0,
        distribution=ContinuousDistribution.NORMAL,
        seed=7,
    )

    rng = np.random.default_rng(7)
    expected_a = rng.normal(loc=10.0, scale=2.0, size=4)
    expected_b = rng.normal(loc=20.0, scale=5.0, size=3)

    np.testing.assert_array_equal(result.group_a, expected_a)
    np.testing.assert_array_equal(result.group_b, expected_b)


@pytest.mark.parametrize(
    "distribution",
    [
        ContinuousDistribution.NORMAL,
        ContinuousDistribution.EXPONENTIAL,
        ContinuousDistribution.LOGNORMAL,
    ],
)
def test_continuous_simulation_empirical_moments_are_reasonable(
    distribution: ContinuousDistribution,
) -> None:
    result = simulate_continuous_ab(
        n_a=50_000,
        n_b=50_000,
        mean_a=10.0,
        mean_b=12.0,
        std_a=2.0,
        std_b=3.0,
        distribution=distribution,
        seed=2026,
    )

    assert math.isclose(float(result.group_a.mean()), 10.0, abs_tol=0.15)
    assert math.isclose(float(result.group_b.mean()), 12.0, abs_tol=0.20)
    assert math.isclose(float(result.group_a.std(ddof=0)), 2.0, abs_tol=0.15)
    assert math.isclose(float(result.group_b.std(ddof=0)), 3.0, abs_tol=0.20)


def test_continuous_simulation_can_add_missing_values() -> None:
    result = simulate_continuous_ab(
        n_a=100,
        n_b=120,
        mean_a=0.0,
        mean_b=1.0,
        std_a=1.0,
        std_b=1.0,
        seed=99,
        missing_rate=0.2,
    )

    missing_a = int(np.isnan(result.group_a).sum())
    missing_b = int(np.isnan(result.group_b).sum())

    assert missing_a > 0
    assert missing_b > 0
    assert result.metadata["missing_count_a"] == missing_a
    assert result.metadata["missing_count_b"] == missing_b


def test_continuous_simulation_can_add_outliers() -> None:
    baseline = simulate_continuous_ab(
        n_a=30,
        n_b=30,
        mean_a=0.0,
        mean_b=0.0,
        std_a=1.0,
        std_b=1.0,
        seed=42,
    )
    contaminated = simulate_continuous_ab(
        n_a=30,
        n_b=30,
        mean_a=0.0,
        mean_b=0.0,
        std_a=1.0,
        std_b=1.0,
        seed=42,
        outlier_rate=1.0,
        outlier_multiplier=10.0,
    )

    assert contaminated.metadata["outlier_count_a"] == 30
    assert contaminated.metadata["outlier_count_b"] == 30
    assert np.min(np.abs(contaminated.group_a - baseline.group_a)) == 10.0
    assert np.min(np.abs(contaminated.group_b - baseline.group_b)) == 10.0


def test_continuous_simulation_serializes_to_json_compatible_payload() -> None:
    result = simulate_continuous_ab(
        n_a=3,
        n_b=2,
        mean_a=0.0,
        mean_b=1.0,
        std_a=1.0,
        std_b=1.0,
        seed=1,
        missing_rate=1.0,
    )

    payload = result.to_dict()

    assert payload["metric_type"] == MetricType.CONTINUOUS.value
    assert payload["group_a"] == [None, None, None]
    assert payload["group_b"] == [None, None]
    assert payload["metadata"]["source"] == "simulation"


@pytest.mark.parametrize(
    ("kwargs", "parameter_name"),
    [
        ({"n_a": 0}, "n_a"),
        ({"n_b": 0}, "n_b"),
        ({"mean_a": math.inf}, "mean_a"),
        ({"mean_b": math.nan}, "mean_b"),
        ({"std_a": 0.0}, "std_a"),
        ({"std_b": -1.0}, "std_b"),
        ({"missing_rate": -0.01}, "missing_rate"),
        ({"outlier_rate": 1.01}, "outlier_rate"),
        ({"outlier_multiplier": 0.0}, "outlier_multiplier"),
    ],
)
def test_continuous_simulation_rejects_invalid_parameters(
    kwargs: dict[str, float | int],
    parameter_name: str,
) -> None:
    params = {
        "n_a": 10,
        "n_b": 10,
        "mean_a": 1.0,
        "mean_b": 2.0,
        "std_a": 1.0,
        "std_b": 1.0,
    } | kwargs

    with pytest.raises(InvalidParameterError) as captured_error:
        simulate_continuous_ab(**params)

    assert parameter_name in captured_error.value.details


def test_continuous_simulation_rejects_unsupported_distribution() -> None:
    with pytest.raises(InvalidParameterError) as captured_error:
        simulate_continuous_ab(
            n_a=10,
            n_b=10,
            mean_a=1.0,
            mean_b=2.0,
            std_a=1.0,
            std_b=1.0,
            distribution="gamma",
        )

    assert captured_error.value.details["distribution"] == "gamma"


def test_lognormal_simulation_rejects_non_positive_target_mean() -> None:
    with pytest.raises(InvalidParameterError) as captured_error:
        simulate_continuous_ab(
            n_a=10,
            n_b=10,
            mean_a=0.0,
            mean_b=2.0,
            std_a=1.0,
            std_b=1.0,
            distribution=ContinuousDistribution.LOGNORMAL,
        )

    assert captured_error.value.details["mean_a"] == 0.0
