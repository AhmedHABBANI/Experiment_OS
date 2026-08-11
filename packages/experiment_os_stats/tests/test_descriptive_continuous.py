"""Tests for continuous descriptive statistics."""

import math

import numpy as np
import pandas as pd
import pytest

from experiment_os_stats import (
    MetricType,
    MissingValuePolicy,
    summarize_continuous_ab,
    summarize_continuous_sample,
)


def test_continuous_sample_summary_matches_numpy_and_pandas() -> None:
    values = np.array([1.0, 2.0, 4.0, 8.0, np.nan])
    clean_values = np.array([1.0, 2.0, 4.0, 8.0])
    pandas_series = pd.Series(clean_values)

    summary = summarize_continuous_sample(values, sample_name="revenue")

    assert summary.sample_name == "revenue"
    assert summary.original_n == 5
    assert summary.n == 4
    assert summary.missing_count == 1
    assert summary.mean == float(np.mean(clean_values))
    assert summary.median == float(np.median(clean_values))
    assert summary.variance == float(np.var(clean_values, ddof=1))
    assert summary.standard_deviation == float(np.std(clean_values, ddof=1))
    assert summary.standard_error == float(np.std(clean_values, ddof=1)) / math.sqrt(4)
    assert summary.minimum == 1.0
    assert summary.maximum == 8.0
    assert summary.q1 == float(pandas_series.quantile(0.25))
    assert summary.q3 == float(pandas_series.quantile(0.75))
    assert summary.iqr == summary.q3 - summary.q1


def test_continuous_singleton_summary_has_zero_sample_spread() -> None:
    summary = summarize_continuous_sample([5.0])

    assert summary.variance == 0.0
    assert summary.standard_deviation == 0.0
    assert summary.standard_error == 0.0
    assert summary.q1 == 5.0
    assert summary.q3 == 5.0


def test_continuous_ab_summary_computes_comparison_metrics() -> None:
    summary = summarize_continuous_ab(
        [1.0, 2.0, 3.0],
        [3.0, 4.0, 5.0],
    )

    assert summary.metric_type is MetricType.CONTINUOUS
    assert summary.group_a.mean == 2.0
    assert summary.group_b.mean == 4.0
    assert summary.comparison.mean_difference == 2.0
    assert summary.comparison.median_difference == 2.0
    assert summary.comparison.mean_ratio == 2.0


def test_continuous_ab_summary_uses_none_for_undefined_mean_ratio() -> None:
    summary = summarize_continuous_ab(
        [-1.0, 0.0, 1.0],
        [2.0, 3.0, 4.0],
    )

    assert summary.group_a.mean == 0.0
    assert summary.comparison.mean_ratio is None


def test_continuous_summary_can_reject_missing_values() -> None:
    with pytest.raises(Exception, match="contains missing observations"):
        summarize_continuous_sample(
            [1.0, np.nan, 3.0],
            missing_policy=MissingValuePolicy.RAISE,
        )


def test_continuous_summary_is_json_compatible() -> None:
    payload = summarize_continuous_ab([1.0, 2.0], [2.0, 4.0]).to_dict()

    assert payload["metric_type"] == "continuous"
    assert payload["group_a"]["n"] == 2
    assert payload["comparison"]["mean_difference"] == 1.5
