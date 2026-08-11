"""Continuous A/B experiment simulation."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import numpy as np

from experiment_os_stats.exceptions import InvalidParameterError
from experiment_os_stats.types import DataSource, MetricType


class ContinuousDistribution(StrEnum):
    """Continuous distributions supported by the simulator."""

    NORMAL = "normal"
    EXPONENTIAL = "exponential"
    LOGNORMAL = "lognormal"


@dataclass(frozen=True, slots=True)
class ContinuousSimulationResult:
    """Simulated continuous A/B observations and reproducibility metadata."""

    group_a: np.ndarray
    group_b: np.ndarray
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the simulated dataset."""
        return {
            "metric_type": MetricType.CONTINUOUS.value,
            "group_a": _to_json_values(self.group_a),
            "group_b": _to_json_values(self.group_b),
            "metadata": dict(self.metadata),
        }


def _to_json_values(values: np.ndarray) -> list[float | None]:
    """Convert an array to strict JSON values."""
    return [None if np.isnan(value) else float(value) for value in values]


def _validate_positive_size(value: int, *, parameter_name: str) -> None:
    """Validate that a group size is a positive integer."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidParameterError(
            "Group sizes must be positive integers.",
            details={parameter_name: value},
        )


def _validate_finite_number(value: float, *, parameter_name: str) -> None:
    """Validate that a parameter is a finite number."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not np.isfinite(value):
        raise InvalidParameterError(
            "Continuous simulation parameters must be finite numbers.",
            details={parameter_name: value},
        )


def _validate_positive_number(value: float, *, parameter_name: str) -> None:
    """Validate that a parameter is a strictly positive finite number."""
    _validate_finite_number(value, parameter_name=parameter_name)

    if value <= 0:
        raise InvalidParameterError(
            "Scale parameters must be strictly positive.",
            details={parameter_name: value},
        )


def _validate_probability(value: float, *, parameter_name: str) -> None:
    """Validate that a parameter is a probability."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not 0 <= value <= 1:
        raise InvalidParameterError(
            "Probability parameters must be between zero and one.",
            details={parameter_name: value},
        )


def _normalize_distribution(distribution: ContinuousDistribution | str) -> ContinuousDistribution:
    """Validate and normalize a requested continuous distribution."""
    try:
        return ContinuousDistribution(distribution)
    except ValueError as error:
        raise InvalidParameterError(
            "Unsupported continuous distribution.",
            details={"distribution": str(distribution)},
        ) from error


def _lognormal_parameters(*, mean: float, std: float, mean_parameter: str) -> tuple[float, float]:
    """Return underlying normal parameters for a lognormal target mean and std."""
    if mean <= 0:
        raise InvalidParameterError(
            "Lognormal target means must be strictly positive.",
            details={mean_parameter: mean},
        )

    variance_ratio = (std / mean) ** 2
    sigma = float(np.sqrt(np.log1p(variance_ratio)))
    mu = float(np.log(mean) - 0.5 * sigma**2)
    return mu, sigma


def _draw_continuous_sample(
    *,
    n: int,
    mean: float,
    std: float,
    distribution: ContinuousDistribution,
    rng: np.random.Generator,
    mean_parameter: str,
) -> np.ndarray:
    """Draw one continuous sample with the requested target moments."""
    if distribution is ContinuousDistribution.NORMAL:
        return rng.normal(loc=mean, scale=std, size=n)

    if distribution is ContinuousDistribution.EXPONENTIAL:
        return rng.exponential(scale=std, size=n) + mean - std

    mu, sigma = _lognormal_parameters(
        mean=mean,
        std=std,
        mean_parameter=mean_parameter,
    )
    return rng.lognormal(mean=mu, sigma=sigma, size=n)


def _add_outliers(
    values: np.ndarray,
    *,
    std: float,
    outlier_rate: float,
    outlier_multiplier: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    """Apply additive outlier contamination to a simulated sample."""
    contaminated = values.astype(float, copy=True)

    if outlier_rate == 0:
        return contaminated, 0

    outlier_mask = rng.random(contaminated.size) < outlier_rate
    outlier_count = int(outlier_mask.sum())
    signs = rng.choice(np.array([-1.0, 1.0]), size=outlier_count)
    contaminated[outlier_mask] += signs * outlier_multiplier * std

    return contaminated, outlier_count


def _add_missing_values(
    values: np.ndarray,
    *,
    missing_rate: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    """Apply missing-value contamination to a simulated sample."""
    contaminated = values.astype(float, copy=True)

    if missing_rate == 0:
        contaminated.setflags(write=False)
        return contaminated, 0

    missing_mask = rng.random(contaminated.size) < missing_rate
    missing_count = int(missing_mask.sum())
    contaminated[missing_mask] = np.nan
    contaminated.setflags(write=False)
    return contaminated, missing_count


def simulate_continuous_ab(
    *,
    n_a: int,
    n_b: int,
    mean_a: float,
    mean_b: float,
    std_a: float,
    std_b: float,
    distribution: ContinuousDistribution | str = ContinuousDistribution.NORMAL,
    seed: int | None = None,
    missing_rate: float = 0.0,
    outlier_rate: float = 0.0,
    outlier_multiplier: float = 6.0,
) -> ContinuousSimulationResult:
    """Simulate independent continuous outcomes for a two-arm A/B experiment."""
    _validate_positive_size(n_a, parameter_name="n_a")
    _validate_positive_size(n_b, parameter_name="n_b")
    _validate_finite_number(mean_a, parameter_name="mean_a")
    _validate_finite_number(mean_b, parameter_name="mean_b")
    _validate_positive_number(std_a, parameter_name="std_a")
    _validate_positive_number(std_b, parameter_name="std_b")
    _validate_probability(missing_rate, parameter_name="missing_rate")
    _validate_probability(outlier_rate, parameter_name="outlier_rate")
    _validate_positive_number(outlier_multiplier, parameter_name="outlier_multiplier")

    normalized_distribution = _normalize_distribution(distribution)
    rng = np.random.default_rng(seed)

    raw_a = _draw_continuous_sample(
        n=n_a,
        mean=mean_a,
        std=std_a,
        distribution=normalized_distribution,
        rng=rng,
        mean_parameter="mean_a",
    )
    raw_b = _draw_continuous_sample(
        n=n_b,
        mean=mean_b,
        std=std_b,
        distribution=normalized_distribution,
        rng=rng,
        mean_parameter="mean_b",
    )

    outlier_a, outlier_count_a = _add_outliers(
        raw_a,
        std=std_a,
        outlier_rate=outlier_rate,
        outlier_multiplier=outlier_multiplier,
        rng=rng,
    )
    outlier_b, outlier_count_b = _add_outliers(
        raw_b,
        std=std_b,
        outlier_rate=outlier_rate,
        outlier_multiplier=outlier_multiplier,
        rng=rng,
    )
    group_a, missing_count_a = _add_missing_values(
        outlier_a,
        missing_rate=missing_rate,
        rng=rng,
    )
    group_b, missing_count_b = _add_missing_values(
        outlier_b,
        missing_rate=missing_rate,
        rng=rng,
    )

    return ContinuousSimulationResult(
        group_a=group_a,
        group_b=group_b,
        metadata={
            "source": DataSource.SIMULATION.value,
            "metric_type": MetricType.CONTINUOUS.value,
            "distribution": normalized_distribution.value,
            "seed": seed,
            "n_a": n_a,
            "n_b": n_b,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "std_a": std_a,
            "std_b": std_b,
            "missing_rate": missing_rate,
            "missing_count_a": missing_count_a,
            "missing_count_b": missing_count_b,
            "outlier_rate": outlier_rate,
            "outlier_multiplier": outlier_multiplier,
            "outlier_count_a": outlier_count_a,
            "outlier_count_b": outlier_count_b,
        },
    )
