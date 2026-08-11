"""Seeded Monte-Carlo safeguards for binary hypothesis tests."""

from collections.abc import Callable

import numpy as np
import pytest

from experiment_os_stats import (
    Alternative,
    StatisticalResult,
    fisher_exact_test,
    two_proportion_z_test,
)

type BinaryTest = Callable[..., StatisticalResult]


def _empirical_rejection_rate(
    test: BinaryTest,
    *,
    seed: int,
    replications: int,
    n_a: int,
    n_b: int,
    p_a: float,
    p_b: float,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Estimate a rejection rate from reproducible binary A/B simulations."""
    rng = np.random.default_rng(seed)
    rejections = 0

    for _ in range(replications):
        group_a = rng.binomial(1, p_a, size=n_a)
        group_b = rng.binomial(1, p_b, size=n_b)
        result = test(group_a, group_b, alternative=alternative)
        rejections += int(result.reject_null is True)

    return rejections / replications


@pytest.mark.parametrize(
    ("test", "minimum_rate", "maximum_rate"),
    [
        (two_proportion_z_test, 0.02, 0.08),
        (fisher_exact_test, 0.0, 0.05),
    ],
)
def test_binary_tests_control_false_positive_rate_under_null(
    test: BinaryTest,
    minimum_rate: float,
    maximum_rate: float,
) -> None:
    false_positive_rate = _empirical_rejection_rate(
        test,
        seed=20260811,
        replications=500,
        n_a=120,
        n_b=120,
        p_a=0.2,
        p_b=0.2,
    )

    assert minimum_rate <= false_positive_rate <= maximum_rate


@pytest.mark.parametrize("test", [two_proportion_z_test, fisher_exact_test])
def test_binary_tests_have_power_for_directional_effect(test: BinaryTest) -> None:
    empirical_power = _empirical_rejection_rate(
        test,
        seed=42017,
        replications=300,
        n_a=120,
        n_b=120,
        p_a=0.15,
        p_b=0.3,
        alternative=Alternative.GREATER,
    )

    assert empirical_power >= 0.75


def test_two_proportion_z_power_increases_with_effect_size() -> None:
    weak_effect_power = _empirical_rejection_rate(
        two_proportion_z_test,
        seed=73021,
        replications=250,
        n_a=150,
        n_b=150,
        p_a=0.2,
        p_b=0.24,
    )
    strong_effect_power = _empirical_rejection_rate(
        two_proportion_z_test,
        seed=73021,
        replications=250,
        n_a=150,
        n_b=150,
        p_a=0.2,
        p_b=0.4,
    )

    assert strong_effect_power >= 0.95
    assert strong_effect_power >= weak_effect_power + 0.5


def test_monte_carlo_validation_is_reproducible() -> None:
    settings = {
        "seed": 9917,
        "replications": 60,
        "n_a": 80,
        "n_b": 80,
        "p_a": 0.2,
        "p_b": 0.3,
    }

    first_rate = _empirical_rejection_rate(two_proportion_z_test, **settings)
    second_rate = _empirical_rejection_rate(two_proportion_z_test, **settings)

    assert first_rate == second_rate
