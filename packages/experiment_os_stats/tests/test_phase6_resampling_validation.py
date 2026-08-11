"""Seeded empirical validation for Phase 6 resampling methods."""

import numpy as np

from experiment_os_stats import (
    Alternative,
    bootstrap_mean_difference,
    permutation_mean_test,
)


def test_mean_percentile_bootstrap_has_reasonable_empirical_coverage() -> None:
    rng = np.random.default_rng(20260813)
    true_difference = 0.5
    covered = 0
    replications = 60

    for replication in range(replications):
        group_a = rng.normal(0.0, 1.0, size=40)
        group_b = rng.normal(true_difference, 1.0, size=40)
        result = bootstrap_mean_difference(
            group_a,
            group_b,
            confidence_level=0.95,
            n_resamples=300,
            seed=50_000 + replication,
        )
        interval = result.confidence_interval
        assert interval is not None
        covered += int(interval.lower <= true_difference <= interval.upper)

    coverage_rate = covered / replications

    assert 0.85 <= coverage_rate <= 1.0


def _permutation_rejection_rate(
    *,
    seed: int,
    replications: int,
    mean_b: float,
    alternative: Alternative,
) -> float:
    """Estimate a seeded rejection rate for the mean permutation test."""
    rng = np.random.default_rng(seed)
    rejections = 0

    for replication in range(replications):
        group_a = rng.normal(0.0, 1.0, size=30)
        group_b = rng.normal(mean_b, 1.0, size=30)
        result = permutation_mean_test(
            group_a,
            group_b,
            alternative=alternative,
            n_permutations=199,
            seed=80_000 + replication,
        )
        rejections += int(result.reject_null is True)

    return rejections / replications


def test_permutation_mean_controls_false_positive_rate_under_null() -> None:
    false_positive_rate = _permutation_rejection_rate(
        seed=61301,
        replications=100,
        mean_b=0.0,
        alternative=Alternative.TWO_SIDED,
    )

    assert 0.01 <= false_positive_rate <= 0.1


def test_permutation_mean_has_power_for_directional_effect() -> None:
    empirical_power = _permutation_rejection_rate(
        seed=61302,
        replications=100,
        mean_b=0.8,
        alternative=Alternative.GREATER,
    )

    assert empirical_power >= 0.75


def test_permutation_p_values_stabilize_with_more_replications() -> None:
    rng = np.random.default_rng(61303)
    group_a = rng.normal(0.0, 1.0, size=25)
    group_b = rng.normal(0.35, 1.0, size=25)
    seeds = range(12)

    low_replication_p_values = np.array(
        [
            permutation_mean_test(
                group_a,
                group_b,
                n_permutations=100,
                seed=seed,
            ).p_value
            for seed in seeds
        ],
        dtype=float,
    )
    high_replication_p_values = np.array(
        [
            permutation_mean_test(
                group_a,
                group_b,
                n_permutations=1_000,
                seed=seed,
            ).p_value
            for seed in seeds
        ],
        dtype=float,
    )

    low_spread = float(np.std(low_replication_p_values, ddof=1))
    high_spread = float(np.std(high_replication_p_values, ddof=1))

    assert high_spread < low_spread * 0.7
