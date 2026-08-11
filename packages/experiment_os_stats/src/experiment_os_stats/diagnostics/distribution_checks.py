"""Data preparation for descriptive diagnostic visualizations."""

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.stats import norm

from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples
from experiment_os_stats.descriptive import summarize_binary_ab, summarize_continuous_ab
from experiment_os_stats.exceptions import InvalidParameterError
from experiment_os_stats.types import MetricType, MissingValuePolicy


@dataclass(frozen=True, slots=True)
class BinaryRatePlotData:
    """Rates and confidence intervals for binary A/B visualization."""

    groups: tuple[str, str]
    proportions: tuple[float, float]
    ci_lower: tuple[float, float]
    ci_upper: tuple[float, float]
    counts: tuple[int, int]
    successes: tuple[int, int]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "groups": list(self.groups),
            "proportions": list(self.proportions),
            "ci_lower": list(self.ci_lower),
            "ci_upper": list(self.ci_upper),
            "counts": list(self.counts),
            "successes": list(self.successes),
        }


@dataclass(frozen=True, slots=True)
class HistogramData:
    """Histogram bin data for one continuous sample."""

    bin_edges: tuple[float, ...]
    counts: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "bin_edges": list(self.bin_edges),
            "counts": list(self.counts),
        }


@dataclass(frozen=True, slots=True)
class BoxplotData:
    """Boxplot summary data for one continuous sample."""

    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-compatible representation."""
        return {
            "minimum": self.minimum,
            "q1": self.q1,
            "median": self.median,
            "q3": self.q3,
            "maximum": self.maximum,
        }


@dataclass(frozen=True, slots=True)
class QQPlotData:
    """Normal QQ plot coordinates for one continuous sample."""

    theoretical_quantiles: tuple[float, ...]
    sample_quantiles: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "theoretical_quantiles": list(self.theoretical_quantiles),
            "sample_quantiles": list(self.sample_quantiles),
        }


@dataclass(frozen=True, slots=True)
class ContinuousDistributionPlotData:
    """Histogram, boxplot and QQ data for continuous A/B visualization."""

    histograms: dict[str, HistogramData]
    boxplots: dict[str, BoxplotData]
    qq_plots: dict[str, QQPlotData]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "histograms": {
                group: histogram.to_dict() for group, histogram in self.histograms.items()
            },
            "boxplots": {group: boxplot.to_dict() for group, boxplot in self.boxplots.items()},
            "qq_plots": {group: qq_plot.to_dict() for group, qq_plot in self.qq_plots.items()},
        }


def _validate_bin_count(bins: int) -> None:
    """Validate a requested histogram bin count."""
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 1:
        raise InvalidParameterError(
            "bins must be a positive integer.",
            details={"bins": bins},
        )


def _histogram(values: np.ndarray, *, bins: int) -> HistogramData:
    """Build histogram data using NumPy's reference implementation."""
    counts, bin_edges = np.histogram(values, bins=bins)
    return HistogramData(
        bin_edges=tuple(float(value) for value in bin_edges),
        counts=tuple(int(value) for value in counts),
    )


def _qq_plot(values: np.ndarray) -> QQPlotData:
    """Build normal QQ plot coordinates for a sample."""
    sorted_values = np.sort(values)
    n = sorted_values.size
    probabilities = (np.arange(1, n + 1) - 0.5) / n
    theoretical_quantiles = norm.ppf(probabilities)

    return QQPlotData(
        theoretical_quantiles=tuple(float(value) for value in theoretical_quantiles),
        sample_quantiles=tuple(float(value) for value in sorted_values),
    )


def binary_rate_plot_data(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    confidence_level: float = 0.95,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> BinaryRatePlotData:
    """Prepare binary rates and intervals for visualization."""
    summary = summarize_binary_ab(
        group_a,
        group_b,
        confidence_level=confidence_level,
        missing_policy=missing_policy,
    )

    return BinaryRatePlotData(
        groups=("A", "B"),
        proportions=(summary.group_a.proportion, summary.group_b.proportion),
        ci_lower=(
            summary.group_a.confidence_interval.lower,
            summary.group_b.confidence_interval.lower,
        ),
        ci_upper=(
            summary.group_a.confidence_interval.upper,
            summary.group_b.confidence_interval.upper,
        ),
        counts=(summary.group_a.n, summary.group_b.n),
        successes=(summary.group_a.successes, summary.group_b.successes),
    )


def continuous_distribution_plot_data(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    bins: int = 10,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> ContinuousDistributionPlotData:
    """Prepare histogram, boxplot and QQ plot data for continuous visualization."""
    _validate_bin_count(bins)
    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.CONTINUOUS,
        missing_policy=missing_policy,
        minimum_size=1,
    )
    summary = summarize_continuous_ab(
        group_a,
        group_b,
        missing_policy=missing_policy,
    )

    return ContinuousDistributionPlotData(
        histograms={
            "A": _histogram(validated.group_a.values, bins=bins),
            "B": _histogram(validated.group_b.values, bins=bins),
        },
        boxplots={
            "A": BoxplotData(
                minimum=summary.group_a.minimum,
                q1=summary.group_a.q1,
                median=summary.group_a.median,
                q3=summary.group_a.q3,
                maximum=summary.group_a.maximum,
            ),
            "B": BoxplotData(
                minimum=summary.group_b.minimum,
                q1=summary.group_b.q1,
                median=summary.group_b.median,
                q3=summary.group_b.q3,
                maximum=summary.group_b.maximum,
            ),
        },
        qq_plots={
            "A": _qq_plot(validated.group_a.values),
            "B": _qq_plot(validated.group_b.values),
        },
    )
