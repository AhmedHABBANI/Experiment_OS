"""Descriptive statistics for binary A/B samples."""

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np
from scipy.stats import norm

from experiment_os_stats.data.normalization import SampleLike
from experiment_os_stats.data.validation import validate_ab_samples, validate_binary_sample
from experiment_os_stats.exceptions import InvalidParameterError
from experiment_os_stats.results import ConfidenceInterval
from experiment_os_stats.types import MetricType, MissingValuePolicy


@dataclass(frozen=True, slots=True)
class BinaryGroupSummary:
    """Descriptive statistics for one binary sample."""

    sample_name: str
    original_n: int
    n: int
    missing_count: int
    successes: int
    failures: int
    proportion: float
    standard_error: float
    confidence_interval: ConfidenceInterval

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "sample_name": self.sample_name,
            "original_n": self.original_n,
            "n": self.n,
            "missing_count": self.missing_count,
            "successes": self.successes,
            "failures": self.failures,
            "proportion": self.proportion,
            "standard_error": self.standard_error,
            "confidence_interval": self.confidence_interval.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class BinaryComparisonSummary:
    """Descriptive comparison between two binary A/B samples."""

    absolute_difference: float
    relative_uplift: float | None
    odds_a: float | None
    odds_b: float | None
    odds_ratio: float | None
    risk_ratio: float | None

    def to_dict(self) -> dict[str, float | None]:
        """Return a JSON-compatible representation."""
        return {
            "absolute_difference": self.absolute_difference,
            "relative_uplift": self.relative_uplift,
            "odds_a": self.odds_a,
            "odds_b": self.odds_b,
            "odds_ratio": self.odds_ratio,
            "risk_ratio": self.risk_ratio,
        }


@dataclass(frozen=True, slots=True)
class BinaryABSummary:
    """Descriptive summary for two binary A/B samples."""

    metric_type: MetricType
    group_a: BinaryGroupSummary
    group_b: BinaryGroupSummary
    comparison: BinaryComparisonSummary

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "metric_type": self.metric_type.value,
            "group_a": self.group_a.to_dict(),
            "group_b": self.group_b.to_dict(),
            "comparison": self.comparison.to_dict(),
        }


def _validate_confidence_level(confidence_level: float) -> None:
    """Validate a confidence level."""
    if not 0 < confidence_level < 1:
        raise InvalidParameterError(
            "confidence_level must be strictly between zero and one.",
            details={"confidence_level": confidence_level},
        )


def _proportion_interval(
    proportion: float,
    n: int,
    *,
    confidence_level: float,
) -> ConfidenceInterval:
    """Compute a clipped Wald confidence interval for one proportion."""
    z_value = float(norm.ppf(0.5 + confidence_level / 2))
    standard_error = sqrt(proportion * (1 - proportion) / n)

    return ConfidenceInterval(
        lower=max(0.0, proportion - z_value * standard_error),
        upper=min(1.0, proportion + z_value * standard_error),
        level=confidence_level,
        parameter="proportion",
        method="wald",
    )


def _odds(proportion: float) -> float | None:
    """Return odds when defined."""
    if proportion >= 1:
        return None

    return proportion / (1 - proportion)


def _ratio(numerator: float, denominator: float) -> float | None:
    """Return a ratio when the denominator is non-zero."""
    if denominator == 0:
        return None

    return numerator / denominator


def summarize_binary_sample(
    values: SampleLike,
    *,
    sample_name: str = "sample",
    confidence_level: float = 0.95,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> BinaryGroupSummary:
    """Compute descriptive statistics for one binary sample."""
    _validate_confidence_level(confidence_level)
    validated = validate_binary_sample(
        values,
        sample_name=sample_name,
        missing_policy=missing_policy,
        minimum_size=1,
    )

    n = int(validated.values.size)
    successes = int(np.sum(validated.values))
    failures = n - successes
    proportion = successes / n
    standard_error = sqrt(proportion * (1 - proportion) / n)

    return BinaryGroupSummary(
        sample_name=sample_name,
        original_n=validated.summary.original_size,
        n=n,
        missing_count=validated.summary.missing_count,
        successes=successes,
        failures=failures,
        proportion=proportion,
        standard_error=standard_error,
        confidence_interval=_proportion_interval(
            proportion,
            n,
            confidence_level=confidence_level,
        ),
    )


def summarize_binary_ab(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    confidence_level: float = 0.95,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
) -> BinaryABSummary:
    """Compute descriptive statistics for two binary A/B samples."""
    _validate_confidence_level(confidence_level)
    validate_ab_samples(
        group_a,
        group_b,
        metric_type=MetricType.BINARY,
        missing_policy=missing_policy,
        minimum_size=1,
    )

    summary_a = summarize_binary_sample(
        group_a,
        sample_name="group_a",
        confidence_level=confidence_level,
        missing_policy=missing_policy,
    )
    summary_b = summarize_binary_sample(
        group_b,
        sample_name="group_b",
        confidence_level=confidence_level,
        missing_policy=missing_policy,
    )

    odds_a = _odds(summary_a.proportion)
    odds_b = _odds(summary_b.proportion)

    return BinaryABSummary(
        metric_type=MetricType.BINARY,
        group_a=summary_a,
        group_b=summary_b,
        comparison=BinaryComparisonSummary(
            absolute_difference=summary_b.proportion - summary_a.proportion,
            relative_uplift=_ratio(
                summary_b.proportion - summary_a.proportion,
                summary_a.proportion,
            ),
            odds_a=odds_a,
            odds_b=odds_b,
            odds_ratio=(
                _ratio(odds_b, odds_a) if odds_a is not None and odds_b is not None else None
            ),
            risk_ratio=_ratio(summary_b.proportion, summary_a.proportion),
        ),
    )
