"""Tests for binary descriptive statistics."""

import math

import numpy as np
import pytest
from statsmodels.stats.proportion import proportion_confint

from experiment_os_stats import (
    InvalidParameterError,
    MetricType,
    MissingValuePolicy,
    summarize_binary_ab,
    summarize_binary_sample,
)


def test_binary_sample_summary_matches_numpy_and_statsmodels() -> None:
    values = np.array([1, 0, 1, 1, 0, np.nan])

    summary = summarize_binary_sample(values, sample_name="conversion")
    lower, upper = proportion_confint(
        count=3,
        nobs=5,
        alpha=0.05,
        method="normal",
    )

    assert summary.sample_name == "conversion"
    assert summary.original_n == 6
    assert summary.n == 5
    assert summary.missing_count == 1
    assert summary.successes == 3
    assert summary.failures == 2
    assert summary.proportion == float(np.nanmean(values))
    assert summary.standard_error == math.sqrt(0.6 * 0.4 / 5)
    assert math.isclose(summary.confidence_interval.lower, max(0.0, lower))
    assert math.isclose(summary.confidence_interval.upper, min(1.0, upper))


def test_binary_ab_summary_computes_comparison_metrics() -> None:
    summary = summarize_binary_ab(
        [1, 0, 1, 0],
        [1, 1, 1, 0],
    )

    assert summary.metric_type is MetricType.BINARY
    assert summary.group_a.proportion == 0.5
    assert summary.group_b.proportion == 0.75
    assert summary.comparison.absolute_difference == 0.25
    assert summary.comparison.relative_uplift == 0.5
    assert summary.comparison.odds_a == 1.0
    assert summary.comparison.odds_b == 3.0
    assert summary.comparison.odds_ratio == 3.0
    assert summary.comparison.risk_ratio == 1.5


def test_binary_ab_summary_uses_none_for_undefined_ratios() -> None:
    summary = summarize_binary_ab(
        [0, 0, 0],
        [1, 1, 1],
    )

    assert summary.comparison.relative_uplift is None
    assert summary.comparison.odds_a == 0.0
    assert summary.comparison.odds_b is None
    assert summary.comparison.odds_ratio is None
    assert summary.comparison.risk_ratio is None


def test_binary_summary_can_reject_missing_values() -> None:
    with pytest.raises(Exception, match="contains missing observations"):
        summarize_binary_sample(
            [1, 0, np.nan],
            missing_policy=MissingValuePolicy.RAISE,
        )


def test_binary_summary_rejects_invalid_confidence_level() -> None:
    with pytest.raises(InvalidParameterError) as captured_error:
        summarize_binary_sample([1, 0, 1], confidence_level=1.0)

    assert captured_error.value.details["confidence_level"] == 1.0


def test_binary_summary_is_json_compatible() -> None:
    payload = summarize_binary_ab([1, 0], [1, 1]).to_dict()

    assert payload["metric_type"] == "binary"
    assert payload["group_a"]["successes"] == 1
    assert payload["comparison"]["absolute_difference"] == 0.5
