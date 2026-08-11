"""Domain-specific exceptions for the ExperimentOS statistical engine."""

from typing import Any


class ExperimentOSError(Exception):
    """Base exception for all errors raised by the statistical engine."""

    code = "EXPERIMENT_OS_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an error with a stable code and optional details."""
        super().__init__(message)

        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the error."""
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }


class DataValidationError(ExperimentOSError):
    """Raised when input data cannot be validated or normalized."""

    code = "DATA_VALIDATION_ERROR"


class IncompatibleMetricError(ExperimentOSError):
    """Raised when a method is incompatible with the supplied metric type."""

    code = "INCOMPATIBLE_METRIC_ERROR"


class InsufficientSampleError(ExperimentOSError):
    """Raised when a sample is too small for the requested analysis."""

    code = "INSUFFICIENT_SAMPLE_ERROR"


class DegenerateSampleError(ExperimentOSError):
    """Raised when a sample contains no usable statistical variation."""

    code = "DEGENERATE_SAMPLE_ERROR"


class InvalidParameterError(ExperimentOSError):
    """Raised when a method receives an invalid configuration parameter."""

    code = "INVALID_PARAMETER_ERROR"
