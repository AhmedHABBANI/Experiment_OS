"""Tests for diagnostic visualization data."""

import math

import numpy as np
import pytest
from scipy.stats import norm

from experiment_os_stats import (
    InvalidParameterError,
    binary_rate_plot_data,
    continuous_distribution_plot_data,
)


def test_binary_rate_plot_data_uses_descriptive_rates_and_intervals() -> None:
    result = binary_rate_plot_data(
        [1, 0, 1, np.nan],
        [1, 1, 1, 0],
    )

    assert result.groups == ("A", "B")
    assert result.proportions == (2 / 3, 0.75)
    assert result.counts == (3, 4)
    assert result.successes == (2, 3)
    assert result.ci_lower[0] < result.proportions[0] < result.ci_upper[0]
    assert result.ci_lower[1] < result.proportions[1] < result.ci_upper[1]


def test_continuous_histogram_data_matches_numpy_reference() -> None:
    group_a = np.array([1.0, 2.0, 3.0, 4.0])
    group_b = np.array([2.0, 4.0, 6.0, 8.0])

    result = continuous_distribution_plot_data(
        group_a,
        group_b,
        bins=2,
    )
    expected_counts_a, expected_edges_a = np.histogram(group_a, bins=2)
    expected_counts_b, expected_edges_b = np.histogram(group_b, bins=2)

    np.testing.assert_array_equal(result.histograms["A"].counts, expected_counts_a)
    np.testing.assert_allclose(result.histograms["A"].bin_edges, expected_edges_a)
    np.testing.assert_array_equal(result.histograms["B"].counts, expected_counts_b)
    np.testing.assert_allclose(result.histograms["B"].bin_edges, expected_edges_b)


def test_continuous_boxplot_data_matches_quantiles() -> None:
    result = continuous_distribution_plot_data(
        [1.0, 2.0, 4.0, 8.0],
        [10.0, 20.0, 30.0, 40.0],
        bins=2,
    )

    assert result.boxplots["A"].minimum == 1.0
    assert result.boxplots["A"].q1 == 1.75
    assert result.boxplots["A"].median == 3.0
    assert result.boxplots["A"].q3 == 5.0
    assert result.boxplots["A"].maximum == 8.0


def test_continuous_qq_plot_data_uses_normal_quantiles() -> None:
    values = np.array([3.0, 1.0, 2.0, 4.0])

    result = continuous_distribution_plot_data(
        values,
        [5.0, 6.0, 7.0, 8.0],
        bins=2,
    )
    expected_probabilities = (np.arange(1, 5) - 0.5) / 4
    expected_theoretical = norm.ppf(expected_probabilities)

    np.testing.assert_allclose(
        result.qq_plots["A"].theoretical_quantiles,
        expected_theoretical,
    )
    np.testing.assert_array_equal(
        result.qq_plots["A"].sample_quantiles,
        np.sort(values),
    )


def test_continuous_distribution_plot_data_rejects_invalid_bins() -> None:
    with pytest.raises(InvalidParameterError) as captured_error:
        continuous_distribution_plot_data(
            [1.0, 2.0],
            [3.0, 4.0],
            bins=0,
        )

    assert captured_error.value.details["bins"] == 0


def test_diagnostic_data_is_json_compatible() -> None:
    binary_payload = binary_rate_plot_data([1, 0], [1, 1]).to_dict()
    continuous_payload = continuous_distribution_plot_data(
        [1.0, 2.0],
        [3.0, 4.0],
        bins=1,
    ).to_dict()

    assert binary_payload["groups"] == ["A", "B"]
    assert binary_payload["successes"] == [1, 2]
    assert continuous_payload["histograms"]["A"]["counts"] == [2]
    assert continuous_payload["boxplots"]["B"]["median"] == 3.5
    assert math.isfinite(continuous_payload["qq_plots"]["A"]["theoretical_quantiles"][0])
