"""Seeded Monte-Carlo safeguards for continuous parametric tests."""

from collections.abc import Callable

import numpy as np
import pytest

from experiment_os_stats import Alternative, StatisticalResult, student_t_test, welch_t_test

type ContinuousTest = Callable[..., StatisticalResult]


def _empirical_rejection_rate(
    test: ContinuousTest,
    *,
    seed: int,
    replications: int,
    n_a: int,
    n_b: int,
    mean_a: float,
    mean_b: float,
    standard_deviation_a: float,
    standard_deviation_b: float,
    alternative: Alternative = Alternative.TWO_SIDED,
) -> float:
    """Estimate a rejection rate from reproducible normal A/B simulations."""
    rng = np.random.default_rng(seed)
    rejections = 0

    for _ in range(replications):
        group_a = rng.normal(mean_a, standard_deviation_a, size=n_a)
        group_b = rng.normal(mean_b, standard_deviation_b, size=n_b)
        result = test(group_a, group_b, alternative=alternative)
        rejections += int(result.reject_null is True)

    return rejections / replications


@pytest.mark.parametrize("test", [student_t_test, welch_t_test])
def test_continuous_t_tests_control_false_positive_rate_with_equal_variances(
    test: ContinuousTest,
) -> None:
    false_positive_rate = _empirical_rejection_rate(
        test,
        seed=20260812,
        replications=500,
        n_a=50,
        n_b=50,
        mean_a=0.0,
        mean_b=0.0,
        standard_deviation_a=1.0,
        standard_deviation_b=1.0,
    )

    assert 0.02 <= false_positive_rate <= 0.08


def test_welch_controls_false_positives_in_unbalanced_unequal_variance_design() -> None:
    settings = {
        "seed": 81173,
        "replications": 500,
        "n_a": 20,
        "n_b": 80,
        "mean_a": 0.0,
        "mean_b": 0.0,
        "standard_deviation_a": 4.0,
        "standard_deviation_b": 1.0,
    }

    student_rate = _empirical_rejection_rate(student_t_test, **settings)
    welch_rate = _empirical_rejection_rate(welch_t_test, **settings)

    assert 0.02 <= welch_rate <= 0.08
    assert student_rate >= 0.2
    assert student_rate >= welch_rate + 0.15


@pytest.mark.parametrize("test", [student_t_test, welch_t_test])
def test_continuous_t_tests_have_power_for_directional_effect(test: ContinuousTest) -> None:
    empirical_power = _empirical_rejection_rate(
        test,
        seed=42018,
        replications=300,
        n_a=50,
        n_b=50,
        mean_a=0.0,
        mean_b=0.6,
        standard_deviation_a=1.0,
        standard_deviation_b=1.0,
        alternative=Alternative.GREATER,
    )

    assert empirical_power >= 0.8


def test_continuous_monte_carlo_validation_is_reproducible() -> None:
    settings = {
        "seed": 9918,
        "replications": 60,
        "n_a": 35,
        "n_b": 45,
        "mean_a": 0.0,
        "mean_b": 0.3,
        "standard_deviation_a": 1.0,
        "standard_deviation_b": 1.5,
    }

    first_rate = _empirical_rejection_rate(welch_t_test, **settings)
    second_rate = _empirical_rejection_rate(welch_t_test, **settings)

    assert first_rate == second_rate
