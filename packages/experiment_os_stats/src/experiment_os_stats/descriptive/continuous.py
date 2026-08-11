"""Descriptive statistics for continuous A/B samples."""

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples, validate_continuous_sample
from experiment_os_stats.types import MetricType, MissingValuePolicy


@dataclass(frozen=True, slots=True)
class ContinuousGroupSummary:
    """Descriptive statistics for one continuous sample."""

    sample_name: str
    original_n: int
    n: int
    missing_count: int
    mean: float
    median: float
    variance: float
    standard_deviation: float
    standard_error: float
    minimum: float
    maximum: float
    q1: float
    q3: float
    iqr: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-compatible representation."""
        return {
            "sample_name": self.sample_name,
            "original_n": self.original_n,
            "n": self.n,
            "missing_count": self.missing_count,
            "mean": self.mean,
            "median": self.median,
            "variance": self.variance,
            "standard_deviation": self.standard_deviation,
            "standard_error": self.standard_error,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "q1": self.q1,
            "q3": self.q3,
            "iqr": self.iqr,
        }


@dataclass(frozen=True, slots=True)
class ContinuousComparisonSummary:
    """Descriptive comparison between two continuous A/B samples."""

    mean_difference: float
    median_difference: float
    mean_ratio: float | None

    def to_dict(self) -> dict[str, float | None]:
        """Return a JSON-compatible representation."""
        return {
            "mean_difference": self.mean_difference,
            "median_difference": self.median_difference,
            "mean_ratio": self.mean_ratio,
        }


@dataclass(frozen=True, slots=True)
class ContinuousABSummary:
    """Descriptive summary for two continuous A/B samples."""

    metric_type: MetricType
    group_a: ContinuousGroupSummary
    group_b: ContinuousGroupSummary
    comparison: ContinuousComparisonSummary

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "metric_type": self.metric_type.value,
            "group_a": self.group_a.to_dict(),
            "group_b": self.group_b.to_dict(),
            "comparison": self.comparison.to_dict(),
        }


def _ratio(numerator: float, denominator: float) -> float | None:
    """Return a ratio when the denominator is non-zero."""
    if denominator == 0:
        return None

    return numerator / denominator


def summarize_continuous_sample(
    values: SampleLike,
    *,
    sample_name: str = "sample",
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> ContinuousGroupSummary:
    """Compute descriptive statistics for one continuous sample."""
    validated = validate_continuous_sample(
        values,
        sample_name=sample_name,
        missing_policy=missing_policy,
        minimum_size=1,
    )
    clean_values = validated.values
    n = int(clean_values.size)
    standard_deviation = float(np.std(clean_values, ddof=1)) if n > 1 else 0.0
    q1, q3 = np.quantile(clean_values, [0.25, 0.75])

    return ContinuousGroupSummary(
        sample_name=sample_name,
        original_n=validated.summary.original_size,
        n=n,
        missing_count=validated.summary.missing_count,
        mean=float(np.mean(clean_values)),
        median=float(np.median(clean_values)),
        variance=float(np.var(clean_values, ddof=1)) if n > 1 else 0.0,
        standard_deviation=standard_deviation,
        standard_error=standard_deviation / sqrt(n),
        minimum=float(np.min(clean_values)),
        maximum=float(np.max(clean_values)),
        q1=float(q1),
        q3=float(q3),
        iqr=float(q3 - q1),
    )


def summarize_continuous_ab(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> ContinuousABSummary:
    """Compute descriptive statistics for two continuous A/B samples."""
    validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.CONTINUOUS,
        missing_policy=missing_policy,
        minimum_size=1,
    )

    summary_a = summarize_continuous_sample(
        group_a,
        sample_name="group_a",
        missing_policy=missing_policy,
    )
    summary_b = summarize_continuous_sample(
        group_b,
        sample_name="group_b",
        missing_policy=missing_policy,
    )

    return ContinuousABSummary(
        metric_type=MetricType.CONTINUOUS,
        group_a=summary_a,
        group_b=summary_b,
        comparison=ContinuousComparisonSummary(
            mean_difference=summary_b.mean - summary_a.mean,
            median_difference=summary_b.median - summary_a.median,
            mean_ratio=_ratio(summary_b.mean, summary_a.mean),
        ),
    )
