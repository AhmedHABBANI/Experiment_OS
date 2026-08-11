"""Tests for ExperimentOS domain-specific exceptions."""

import pytest

from experiment_os_stats import (
    DataValidationError,
    DegenerateSampleError,
    ExperimentOSError,
    IncompatibleMetricError,
    InsufficientSampleError,
    InvalidParameterError,
)


def test_base_error_preserves_message_and_details() -> None:
    error = ExperimentOSError(
        "The operation could not be completed.",
        details={
            "operation": "example",
            "attempt": 1,
        },
    )

    assert str(error) == "The operation could not be completed."
    assert error.message == "The operation could not be completed."
    assert error.details == {
        "operation": "example",
        "attempt": 1,
    }


def test_error_can_be_converted_to_dictionary() -> None:
    error = InsufficientSampleError(
        "At least two observations are required.",
        details={
            "group": "A",
            "observed_size": 1,
            "minimum_size": 2,
        },
    )

    assert error.to_dict() == {
        "code": "INSUFFICIENT_SAMPLE_ERROR",
        "message": "At least two observations are required.",
        "details": {
            "group": "A",
            "observed_size": 1,
            "minimum_size": 2,
        },
    }


@pytest.mark.parametrize(
    ("error_class", "expected_code"),
    [
        (DataValidationError, "DATA_VALIDATION_ERROR"),
        (IncompatibleMetricError, "INCOMPATIBLE_METRIC_ERROR"),
        (InsufficientSampleError, "INSUFFICIENT_SAMPLE_ERROR"),
        (DegenerateSampleError, "DEGENERATE_SAMPLE_ERROR"),
        (InvalidParameterError, "INVALID_PARAMETER_ERROR"),
    ],
)
def test_specialized_errors_have_stable_codes(
    error_class: type[ExperimentOSError],
    expected_code: str,
) -> None:
    error = error_class("Example error.")

    assert isinstance(error, ExperimentOSError)
    assert error.code == expected_code


def test_error_without_details_uses_empty_dictionary() -> None:
    error = DataValidationError("Invalid input data.")

    assert error.details == {}
    assert error.to_dict()["details"] == {}
