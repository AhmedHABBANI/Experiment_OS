"""Standard result models returned by ExperimentOS statistical methods."""

from dataclasses import dataclass, field
from math import isnan
from typing import Any

from experiment_os_stats.types import Alternative, MetricType, WarningSeverity


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    """Confidence interval associated with an estimated parameter."""

    lower: float
    upper: float
    level: float = 0.95
    parameter: str | None = None
    method: str | None = None

    def __post_init__(self) -> None:
        """Validate the confidence interval."""
        if not 0 < self.level < 1:
            raise ValueError("Confidence level must be strictly between 0 and 1.")

        if isnan(self.lower) or isnan(self.upper):
            raise ValueError("Confidence interval boundaries cannot be NaN.")

        if self.lower > self.upper:
            raise ValueError("The lower confidence bound cannot exceed the upper bound.")

    def to_dict(self) -> dict[str, float | str | None]:
        """Return a JSON-compatible representation."""
        return {
            "lower": self.lower,
            "upper": self.upper,
            "level": self.level,
            "parameter": self.parameter,
            "method": self.method,
        }


@dataclass(frozen=True, slots=True)
class StatisticalWarning:
    """Structured warning produced during a statistical analysis."""

    code: str
    message: str
    severity: WarningSeverity = WarningSeverity.WARNING
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the warning."""
        if not self.code.strip():
            raise ValueError("Warning code cannot be empty.")

        if not self.message.strip():
            raise ValueError("Warning message cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class StatisticalResult:
    """Standard result returned by an ExperimentOS statistical method."""

    test_name: str
    metric_type: MetricType
    alpha: float
    alternative: Alternative

    statistic: float | None = None
    p_value: float | None = None
    estimate: float | None = None
    confidence_interval: ConfidenceInterval | None = None

    effect_size: float | None = None
    effect_size_name: str | None = None

    reject_null: bool | None = None

    assumptions: tuple[str, ...] = ()
    warnings: tuple[StatisticalWarning, ...] = ()

    interpretation: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the result and infer the hypothesis-test decision."""
        if not self.test_name.strip():
            raise ValueError("test_name cannot be empty.")

        if not 0 < self.alpha < 1:
            raise ValueError("alpha must be strictly between 0 and 1.")

        if self.p_value is not None:
            if isnan(self.p_value) or not 0 <= self.p_value <= 1:
                raise ValueError("p_value must be a finite value between 0 and 1.")

            inferred_decision = self.p_value < self.alpha

            if self.reject_null is None:
                object.__setattr__(
                    self,
                    "reject_null",
                    inferred_decision,
                )
            elif self.reject_null is not inferred_decision:
                raise ValueError("reject_null is inconsistent with p_value and alpha.")

        if self.effect_size is not None and not self.effect_size_name:
            raise ValueError("effect_size_name is required when effect_size is provided.")

        if self.effect_size is None and self.effect_size_name is not None:
            raise ValueError("effect_size must be provided when effect_size_name is set.")

        if any(not assumption.strip() for assumption in self.assumptions):
            raise ValueError("Assumptions cannot contain empty strings.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the result."""
        return {
            "test_name": self.test_name,
            "metric_type": self.metric_type.value,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "alpha": self.alpha,
            "alternative": self.alternative.value,
            "estimate": self.estimate,
            "confidence_interval": (
                self.confidence_interval.to_dict() if self.confidence_interval is not None else None
            ),
            "effect_size": self.effect_size,
            "effect_size_name": self.effect_size_name,
            "reject_null": self.reject_null,
            "assumptions": list(self.assumptions),
            "warnings": [warning.to_dict() for warning in self.warnings],
            "interpretation": dict(self.interpretation),
            "metadata": dict(self.metadata),
        }
