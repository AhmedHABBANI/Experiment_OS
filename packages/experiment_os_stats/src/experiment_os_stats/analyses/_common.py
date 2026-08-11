"""Shared parameter validation for statistical analyses."""

from experiment_os_stats.exceptions import InvalidParameterError
from experiment_os_stats.types import Alternative


def validate_alpha(alpha: float) -> None:
    """Validate a significance level."""
    if not 0 < alpha < 1:
        raise InvalidParameterError(
            "alpha must be strictly between zero and one.",
            details={"alpha": alpha},
        )


def normalize_alternative(alternative: Alternative | str) -> Alternative:
    """Normalize an alternative hypothesis or raise a domain error."""
    try:
        return Alternative(alternative)
    except ValueError as error:
        raise InvalidParameterError(
            "Unsupported alternative hypothesis.",
            details={"alternative": str(alternative)},
        ) from error
