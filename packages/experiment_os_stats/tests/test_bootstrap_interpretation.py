"""Tests for deterministic bootstrap-estimation interpretation."""

from experiment_os_stats import (
    StatisticalInterpretation,
    bootstrap_mean_difference,
    bootstrap_median_difference,
)
from experiment_os_stats.interpretation import interpret_bootstrap_difference_result


def test_bootstrap_mean_interpretation_describes_estimation_only_contract() -> None:
    result = bootstrap_mean_difference(
        [1.0, 2.0, 3.0, 4.0],
        [5.0, 6.0, 7.0, 8.0],
        n_resamples=500,
        seed=42,
    )

    assert isinstance(result.interpretation, StatisticalInterpretation)
    assert "mean difference" in result.interpretation.question
    assert "does not test a null hypothesis" in result.interpretation.null_hypothesis
    assert "neither a p-value" in result.interpretation.decision
    assert "4 units higher" in result.interpretation.effect
    assert "interval lies entirely above zero" in result.interpretation.uncertainty


def test_bootstrap_median_interpretation_uses_median_estimand() -> None:
    result = bootstrap_median_difference(
        [5.0, 6.0, 7.0, 8.0],
        [1.0, 2.0, 3.0, 4.0],
        n_resamples=500,
        seed=7,
    )

    assert "median difference" in result.interpretation.question
    assert "4 units lower" in result.interpretation.effect
    assert "interval lies entirely below zero" in result.interpretation.uncertainty


def test_bootstrap_interpretation_contextualizes_interval_including_zero() -> None:
    interpretation = interpret_bootstrap_difference_result(
        estimand="mean",
        estimate=0.2,
        lower=-1.0,
        upper=1.4,
        confidence_level=0.95,
        standard_error=0.6,
        n_resamples=1_000,
        seed=9,
    )

    assert "95% percentile bootstrap interval is [-1, 1.4]" in interpretation.uncertainty
    assert "includes zero" in interpretation.uncertainty
    assert "either no difference or a difference" in interpretation.uncertainty


def test_bootstrap_interpretation_reports_precision_and_reproducibility() -> None:
    interpretation = interpret_bootstrap_difference_result(
        estimand="median",
        estimate=2.0,
        lower=0.5,
        upper=3.5,
        confidence_level=0.9,
        standard_error=0.75,
        n_resamples=2_000,
        seed=812,
    )

    assert "90% percentile" in interpretation.uncertainty
    assert "standard error 0.75" in interpretation.uncertainty
    assert "2000 independent within-group resamples" in interpretation.uncertainty
    assert "Seed 812" in interpretation.uncertainty


def test_bootstrap_interpretation_discloses_unseeded_non_reproducibility() -> None:
    result = bootstrap_mean_difference(
        [1.0, 2.0, 3.0],
        [2.0, 3.0, 4.0],
        n_resamples=100,
    )

    assert "No seed was provided" in result.interpretation.uncertainty
    assert "not guaranteed" in result.interpretation.uncertainty


def test_zero_bootstrap_effect_and_point_interval_are_neutral() -> None:
    result = bootstrap_median_difference(
        [1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0],
        n_resamples=100,
        seed=3,
    )

    assert "difference of 0 units" in result.interpretation.effect
    assert "[0, 0]" in result.interpretation.uncertainty
    assert "includes zero" in result.interpretation.uncertainty
    assert "not assessed" in result.interpretation.practical_significance
