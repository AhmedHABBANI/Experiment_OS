"""Tests for binary A/B simulation."""

import math

import numpy as np
import pytest

from experiment_os_stats import InvalidParameterError, MetricType, simulate_binary_ab


def test_binary_simulation_is_reproducible_with_seed() -> None:
    first = simulate_binary_ab(
        n_a=20,
        n_b=30,
        p_a=0.25,
        p_b=0.4,
        seed=123,
        missing_rate=0.1,
    )
    second = simulate_binary_ab(
        n_a=20,
        n_b=30,
        p_a=0.25,
        p_b=0.4,
        seed=123,
        missing_rate=0.1,
    )

    np.testing.assert_array_equal(first.group_a, second.group_a)
    np.testing.assert_array_equal(first.group_b, second.group_b)
    assert first.metadata == second.metadata


def test_binary_simulation_preserves_requested_group_sizes() -> None:
    result = simulate_binary_ab(
        n_a=11,
        n_b=17,
        p_a=0.2,
        p_b=0.8,
        seed=42,
    )

    assert result.group_a.shape == (11,)
    assert result.group_b.shape == (17,)
    assert result.metadata["n_a"] == 11
    assert result.metadata["n_b"] == 17


def test_binary_simulation_matches_numpy_reference_for_seeded_draws() -> None:
    result = simulate_binary_ab(
        n_a=6,
        n_b=5,
        p_a=0.3,
        p_b=0.7,
        seed=7,
    )

    rng = np.random.default_rng(7)
    expected_a = rng.binomial(1, 0.3, size=6).astype(float)
    expected_b = rng.binomial(1, 0.7, size=5).astype(float)

    np.testing.assert_array_equal(result.group_a, expected_a)
    np.testing.assert_array_equal(result.group_b, expected_b)


def test_binary_simulation_empirical_proportions_are_reasonable() -> None:
    result = simulate_binary_ab(
        n_a=10_000,
        n_b=10_000,
        p_a=0.25,
        p_b=0.65,
        seed=2026,
    )

    assert math.isclose(float(result.group_a.mean()), 0.25, abs_tol=0.02)
    assert math.isclose(float(result.group_b.mean()), 0.65, abs_tol=0.02)


def test_binary_simulation_can_add_missing_values() -> None:
    result = simulate_binary_ab(
        n_a=100,
        n_b=120,
        p_a=0.5,
        p_b=0.5,
        seed=99,
        missing_rate=0.2,
    )

    missing_a = int(np.isnan(result.group_a).sum())
    missing_b = int(np.isnan(result.group_b).sum())

    assert missing_a > 0
    assert missing_b > 0
    assert result.metadata["missing_count_a"] == missing_a
    assert result.metadata["missing_count_b"] == missing_b


def test_binary_simulation_serializes_to_json_compatible_payload() -> None:
    result = simulate_binary_ab(
        n_a=3,
        n_b=2,
        p_a=0.5,
        p_b=0.5,
        seed=1,
        missing_rate=1.0,
    )

    payload = result.to_dict()

    assert payload["metric_type"] == MetricType.BINARY.value
    assert payload["group_a"] == [None, None, None]
    assert payload["group_b"] == [None, None]
    assert payload["metadata"]["source"] == "simulation"


@pytest.mark.parametrize(
    ("kwargs", "parameter_name"),
    [
        ({"n_a": 0}, "n_a"),
        ({"n_b": 0}, "n_b"),
        ({"p_a": -0.1}, "p_a"),
        ({"p_b": 1.1}, "p_b"),
        ({"missing_rate": -0.01}, "missing_rate"),
        ({"missing_rate": 1.01}, "missing_rate"),
    ],
)
def test_binary_simulation_rejects_invalid_parameters(
    kwargs: dict[str, float | int],
    parameter_name: str,
) -> None:
    params = {
        "n_a": 10,
        "n_b": 10,
        "p_a": 0.4,
        "p_b": 0.6,
    } | kwargs

    with pytest.raises(InvalidParameterError) as captured_error:
        simulate_binary_ab(**params)

    assert parameter_name in captured_error.value.details
