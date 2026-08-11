"""Tests for sample normalization and validation."""

import numpy as np
import pandas as pd
import pytest

from experiment_os_stats import (
    DataValidationError,
    DegenerateSampleError,
    InsufficientSampleError,
    InvalidParameterError,
    MetricType,
    MissingValuePolicy,
    validate_ab_samples,
    validate_binary_sample,
    validate_continuous_sample,
)


def test_continuous_sample_accepts_python_list() -> None:
    result = validate_continuous_sample([1, 2.5, 4])

    np.testing.assert_array_equal(
        result.values,
        np.array([1.0, 2.5, 4.0]),
    )
    assert result.summary.valid_size == 3
    assert result.summary.metric_type is MetricType.CONTINUOUS


def test_continuous_sample_accepts_pandas_series() -> None:
    result = validate_continuous_sample(
        pd.Series([1.0, 2.0, 3.0]),
    )

    assert result.summary.original_size == 3
    assert result.summary.has_variation is True


def test_continuous_sample_drops_missing_values_by_default() -> None:
    result = validate_continuous_sample(
        [1.0, np.nan, 3.0],
    )

    np.testing.assert_array_equal(
        result.values,
        np.array([1.0, 3.0]),
    )
    assert result.summary.original_size == 3
    assert result.summary.valid_size == 2
    assert result.summary.missing_count == 1


def test_missing_value_policy_can_reject_missing_values() -> None:
    with pytest.raises(
        DataValidationError,
        match="contains missing observations",
    ):
        validate_continuous_sample(
            [1.0, np.nan, 3.0],
            missing_policy=MissingValuePolicy.RAISE,
        )


def test_continuous_sample_rejects_boolean_values() -> None:
    with pytest.raises(
        DataValidationError,
        match="Boolean observations are not valid",
    ):
        validate_continuous_sample([True, False, True])


def test_continuous_sample_rejects_non_numeric_values() -> None:
    with pytest.raises(
        DataValidationError,
        match="cannot be converted to numbers",
    ):
        validate_continuous_sample([1.0, "invalid", 3.0])


def test_sample_rejects_two_dimensional_array() -> None:
    with pytest.raises(
        DataValidationError,
        match="must be one-dimensional",
    ):
        validate_continuous_sample(
            np.array([[1.0, 2.0], [3.0, 4.0]]),
        )


def test_sample_rejects_infinite_values() -> None:
    with pytest.raises(
        DataValidationError,
        match="Infinite observations are not supported",
    ):
        validate_continuous_sample([1.0, np.inf, 3.0])


def test_binary_sample_accepts_zero_one_and_booleans() -> None:
    result = validate_binary_sample(
        [0, 1, True, False],
    )

    np.testing.assert_array_equal(
        result.values,
        np.array([0, 1, 1, 0], dtype=np.int8),
    )
    assert result.summary.metric_type is MetricType.BINARY


def test_binary_sample_rejects_other_values() -> None:
    with pytest.raises(
        DataValidationError,
        match="may contain only zero and one",
    ) as captured_error:
        validate_binary_sample([0, 1, 2, -1])

    assert captured_error.value.details["invalid_values"] == [-1.0, 2.0]


def test_minimum_sample_size_is_enforced() -> None:
    with pytest.raises(
        InsufficientSampleError,
        match="does not contain enough usable observations",
    ):
        validate_continuous_sample(
            [1.0],
            minimum_size=2,
        )


def test_invalid_minimum_size_is_rejected() -> None:
    with pytest.raises(
        InvalidParameterError,
        match="minimum_size must be greater",
    ):
        validate_continuous_sample(
            [1.0, 2.0],
            minimum_size=0,
        )


def test_variation_can_be_required() -> None:
    with pytest.raises(
        DegenerateSampleError,
        match="contains no statistical variation",
    ):
        validate_continuous_sample(
            [3.0, 3.0, 3.0],
            require_variation=True,
        )


def test_constant_binary_sample_is_allowed_by_default() -> None:
    result = validate_binary_sample([1, 1, 1])

    assert result.summary.has_variation is False
    assert result.summary.unique_count == 1


def test_summary_is_json_compatible() -> None:
    result = validate_continuous_sample(
        [1.0, 2.0, np.nan, 4.0],
        sample_name="revenue",
    )

    assert result.summary.to_dict() == {
        "sample_name": "revenue",
        "metric_type": "continuous",
        "original_size": 4,
        "valid_size": 3,
        "missing_count": 1,
        "unique_count": 3,
        "has_variation": True,
        "minimum": 1.0,
        "maximum": 4.0,
    }


def test_validated_values_are_read_only() -> None:
    result = validate_continuous_sample([1.0, 2.0, 3.0])

    with pytest.raises(ValueError):
        result.values[0] = 99.0


def test_validate_ab_samples_dispatches_continuous_validation() -> None:
    result = validate_ab_samples(
        [1.0, 2.0, 3.0],
        [2.0, 3.0, 4.0],
        metric_type=MetricType.CONTINUOUS,
    )

    assert result.metric_type is MetricType.CONTINUOUS
    assert result.group_a.summary.sample_name == "group_a"
    assert result.group_b.summary.sample_name == "group_b"


def test_validate_ab_samples_dispatches_binary_validation() -> None:
    result = validate_ab_samples(
        [0, 1, 1],
        [0, 0, 1],
        metric_type=MetricType.BINARY,
    )

    assert result.metric_type is MetricType.BINARY
    assert result.group_a.values.dtype == np.int8
    assert result.group_b.values.dtype == np.int8


def test_validate_ab_samples_enforces_group_size() -> None:
    with pytest.raises(InsufficientSampleError) as captured_error:
        validate_ab_samples(
            [1.0],
            [2.0, 3.0],
            metric_type=MetricType.CONTINUOUS,
        )

    assert captured_error.value.details["sample_name"] == "group_a"
    assert captured_error.value.details["minimum_size"] == 2
