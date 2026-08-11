"""Binary A/B experiment simulation."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from experiment_os_stats.exceptions import InvalidParameterError
from experiment_os_stats.types import DataSource, MetricType


@dataclass(frozen=True, slots=True)
class BinarySimulationResult:
    """Simulated binary A/B observations and reproducibility metadata."""

    group_a: np.ndarray
    group_b: np.ndarray
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the simulated dataset."""
        return {
            "metric_type": MetricType.BINARY.value,
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


def _validate_probability(value: float, *, parameter_name: str) -> None:
    """Validate that a parameter is a probability."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not 0 <= value <= 1:
        raise InvalidParameterError(
            "Probability parameters must be between zero and one.",
            details={parameter_name: value},
        )


def _add_missing_values(
    values: np.ndarray,
    *,
    missing_rate: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Apply missing-value contamination to a simulated sample."""
    contaminated = values.astype(float, copy=True)

    if missing_rate > 0:
        missing_mask = rng.random(contaminated.size) < missing_rate
        contaminated[missing_mask] = np.nan

    contaminated.setflags(write=False)
    return contaminated


def simulate_binary_ab(
    *,
    n_a: int,
    n_b: int,
    p_a: float,
    p_b: float,
    seed: int | None = None,
    missing_rate: float = 0.0,
) -> BinarySimulationResult:
    """Simulate independent binary outcomes for a two-arm A/B experiment."""
    _validate_positive_size(n_a, parameter_name="n_a")
    _validate_positive_size(n_b, parameter_name="n_b")
    _validate_probability(p_a, parameter_name="p_a")
    _validate_probability(p_b, parameter_name="p_b")
    _validate_probability(missing_rate, parameter_name="missing_rate")

    rng = np.random.default_rng(seed)
    raw_a = rng.binomial(1, p_a, size=n_a)
    raw_b = rng.binomial(1, p_b, size=n_b)

    group_a = _add_missing_values(
        raw_a,
        missing_rate=missing_rate,
        rng=rng,
    )
    group_b = _add_missing_values(
        raw_b,
        missing_rate=missing_rate,
        rng=rng,
    )

    return BinarySimulationResult(
        group_a=group_a,
        group_b=group_b,
        metadata={
            "source": DataSource.SIMULATION.value,
            "metric_type": MetricType.BINARY.value,
            "seed": seed,
            "n_a": n_a,
            "n_b": n_b,
            "p_a": p_a,
            "p_b": p_b,
            "missing_rate": missing_rate,
            "missing_count_a": int(np.isnan(group_a).sum()),
            "missing_count_b": int(np.isnan(group_b).sum()),
        },
    )
