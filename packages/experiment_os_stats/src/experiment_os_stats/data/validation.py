"""Validation models and functions for statistical samples."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from experiment_os_stats.data.normalization import (
    SampleLike,
    handle_missing_values,
    to_1d_float_array,
)
from experiment_os_stats.exceptions import (
    DataValidationError,
    DegenerateSampleError,
    InsufficientSampleError,
    InvalidParameterError,
)
from experiment_os_stats.types import MetricType, MissingValuePolicy


@dataclass(frozen=True, slots=True)
class SampleValidationSummary:
    """Summary produced after validating one statistical sample."""

    sample_name: str
    metric_type: MetricType
    original_size: int
    valid_size: int
    missing_count: int
    unique_count: int
    has_variation: bool
    minimum: float | None
    maximum: float | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "sample_name": self.sample_name,
            "metric_type": self.metric_type.value,
            "original_size": self.original_size,
            "valid_size": self.valid_size,
            "missing_count": self.missing_count,
            "unique_count": self.unique_count,
            "has_variation": self.has_variation,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True, slots=True)
class ValidatedSample:
    """Validated observations and their validation summary."""

    values: np.ndarray
    summary: SampleValidationSummary


@dataclass(frozen=True, slots=True)
class ValidatedABData:
    """Validated independent groups A and B."""

    metric_type: MetricType
    group_a: ValidatedSample
    group_b: ValidatedSample


def _validate_minimum_size(minimum_size: int) -> None:
    """Validate a requested minimum sample size."""
    if minimum_size < 1:
        raise InvalidParameterError(
            "minimum_size must be greater than or equal to one.",
            details={"minimum_size": minimum_size},
        )


def _build_summary(
    values: np.ndarray,
    *,
    sample_name: str,
    metric_type: MetricType,
    original_size: int,
    missing_count: int,
) -> SampleValidationSummary:
    """Build a summary for a validated sample."""
    unique_count = int(np.unique(values).size)

    return SampleValidationSummary(
        sample_name=sample_name,
        metric_type=metric_type,
        original_size=original_size,
        valid_size=int(values.size),
        missing_count=missing_count,
        unique_count=unique_count,
        has_variation=unique_count > 1,
        minimum=float(np.min(values)) if values.size else None,
        maximum=float(np.max(values)) if values.size else None,
    )


def _validate_sample_size(
    values: np.ndarray,
    *,
    sample_name: str,
    minimum_size: int,
) -> None:
    """Ensure that a sample contains enough usable observations."""
    if values.size < minimum_size:
        raise InsufficientSampleError(
            "The sample does not contain enough usable observations.",
            details={
                "sample_name": sample_name,
                "observed_size": int(values.size),
                "minimum_size": minimum_size,
            },
        )


def _validate_variation(
    summary: SampleValidationSummary,
    *,
    require_variation: bool,
) -> None:
    """Reject a constant sample when variation is required."""
    if require_variation and not summary.has_variation:
        raise DegenerateSampleError(
            "The sample contains no statistical variation.",
            details={
                "sample_name": summary.sample_name,
                "unique_count": summary.unique_count,
            },
        )


def validate_continuous_sample(
    values: SampleLike,
    *,
    sample_name: str = "sample",
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
    minimum_size: int = 1,
    require_variation: bool = False,
) -> ValidatedSample:
    """Validate and normalize a continuous statistical sample."""
    _validate_minimum_size(minimum_size)

    normalized = to_1d_float_array(
        values,
        sample_name=sample_name,
        allow_boolean=False,
    )
    original_size = int(normalized.size)

    cleaned, missing_count = handle_missing_values(
        normalized,
        sample_name=sample_name,
        policy=missing_policy,
    )

    _validate_sample_size(
        cleaned,
        sample_name=sample_name,
        minimum_size=minimum_size,
    )

    summary = _build_summary(
        cleaned,
        sample_name=sample_name,
        metric_type=MetricType.CONTINUOUS,
        original_size=original_size,
        missing_count=missing_count,
    )

    _validate_variation(
        summary,
        require_variation=require_variation,
    )

    return ValidatedSample(
        values=cleaned,
        summary=summary,
    )


def validate_binary_sample(
    values: SampleLike,
    *,
    sample_name: str = "sample",
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
    minimum_size: int = 1,
    require_variation: bool = False,
) -> ValidatedSample:
    """Validate and normalize a binary statistical sample."""
    _validate_minimum_size(minimum_size)

    normalized = to_1d_float_array(
        values,
        sample_name=sample_name,
        allow_boolean=True,
    )
    original_size = int(normalized.size)

    cleaned, missing_count = handle_missing_values(
        normalized,
        sample_name=sample_name,
        policy=missing_policy,
    )

    _validate_sample_size(
        cleaned,
        sample_name=sample_name,
        minimum_size=minimum_size,
    )

    valid_binary_mask = np.isin(cleaned, (0.0, 1.0))

    if not valid_binary_mask.all():
        invalid_values = sorted(float(value) for value in np.unique(cleaned[~valid_binary_mask]))

        raise DataValidationError(
            "A binary sample may contain only zero and one.",
            details={
                "sample_name": sample_name,
                "invalid_values": invalid_values,
            },
        )

    binary_values = cleaned.astype(np.int8, copy=True)
    binary_values.setflags(write=False)

    summary = _build_summary(
        binary_values,
        sample_name=sample_name,
        metric_type=MetricType.BINARY,
        original_size=original_size,
        missing_count=missing_count,
    )

    _validate_variation(
        summary,
        require_variation=require_variation,
    )

    return ValidatedSample(
        values=binary_values,
        summary=summary,
    )


def validate_ab_samples(
    group_a: SampleLike,
    group_b: SampleLike,
    *,
    metric_type: MetricType,
    missing_policy: MissingValuePolicy = MissingValuePolicy.DROP,
    minimum_size: int = 2,
    require_variation: bool = False,
) -> ValidatedABData:
    """Validate two independent A/B samples."""
    try:
        normalized_metric_type = MetricType(metric_type)
    except ValueError as error:
        raise InvalidParameterError(
            "Unsupported metric type.",
            details={"metric_type": str(metric_type)},
        ) from error

    validator = (
        validate_binary_sample
        if normalized_metric_type is MetricType.BINARY
        else validate_continuous_sample
    )

    validated_a = validator(
        group_a,
        sample_name="group_a",
        missing_policy=missing_policy,
        minimum_size=minimum_size,
        require_variation=require_variation,
    )

    validated_b = validator(
        group_b,
        sample_name="group_b",
        missing_policy=missing_policy,
        minimum_size=minimum_size,
        require_variation=require_variation,
    )

    return ValidatedABData(
        metric_type=normalized_metric_type,
        group_a=validated_a,
        group_b=validated_b,
    )
