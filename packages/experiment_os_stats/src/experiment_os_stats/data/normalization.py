"""Low-level utilities for normalizing statistical samples."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from experiment_os_stats.exceptions import DataValidationError
from experiment_os_stats.types import MissingValuePolicy

type SampleLike = Sequence[object] | np.ndarray | pd.Series


def _contains_boolean(values: np.ndarray) -> bool:
    """Return whether an array contains explicit Boolean values."""
    if np.issubdtype(values.dtype, np.bool_):
        return True

    if values.dtype != object:
        return False

    return any(isinstance(value, (bool, np.bool_)) for value in values if value is not None)


def to_1d_float_array(
    values: SampleLike,
    *,
    sample_name: str,
    allow_boolean: bool = False,
) -> np.ndarray:
    """Convert a supported sample to a one-dimensional float array."""
    if isinstance(values, (str, bytes)):
        raise DataValidationError(
            "A sample must be a collection of observations, not a string.",
            details={"sample_name": sample_name},
        )

    raw_values = np.asarray(values)

    if raw_values.ndim != 1:
        raise DataValidationError(
            "A sample must be one-dimensional.",
            details={
                "sample_name": sample_name,
                "observed_dimensions": int(raw_values.ndim),
            },
        )

    if np.iscomplexobj(raw_values):
        raise DataValidationError(
            "Complex-valued observations are not supported.",
            details={"sample_name": sample_name},
        )

    if not allow_boolean and _contains_boolean(raw_values):
        raise DataValidationError(
            "Boolean observations are not valid continuous values.",
            details={"sample_name": sample_name},
        )

    try:
        normalized = raw_values.astype(float, copy=True)
    except (TypeError, ValueError) as error:
        raise DataValidationError(
            "The sample contains values that cannot be converted to numbers.",
            details={"sample_name": sample_name},
        ) from error

    return normalized


def handle_missing_values(
    values: np.ndarray,
    *,
    sample_name: str,
    policy: MissingValuePolicy,
) -> tuple[np.ndarray, int]:
    """Apply a missing-value policy and reject infinite observations."""
    infinite_mask = np.isinf(values)

    if infinite_mask.any():
        raise DataValidationError(
            "Infinite observations are not supported.",
            details={
                "sample_name": sample_name,
                "infinite_count": int(infinite_mask.sum()),
            },
        )

    missing_mask = np.isnan(values)
    missing_count = int(missing_mask.sum())

    if missing_count > 0 and policy is MissingValuePolicy.RAISE:
        raise DataValidationError(
            "The sample contains missing observations.",
            details={
                "sample_name": sample_name,
                "missing_count": missing_count,
                "missing_policy": policy.value,
            },
        )

    cleaned_values = values[~missing_mask].copy()
    cleaned_values.setflags(write=False)

    return cleaned_values, missing_count
