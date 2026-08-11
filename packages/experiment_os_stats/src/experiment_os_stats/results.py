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
class StatisticalInterpretation:
    """Stable deterministic interpretation attached to a statistical result."""

    null_hypothesis: str
    alternative_hypothesis: str
    question: str | None = None
    decision: str | None = None
    effect: str | None = None
    uncertainty: str | None = None
    practical_significance: str | None = None
    warning_context: str | None = None

    def __post_init__(self) -> None:
        """Reject empty required hypotheses and blank optional messages."""
        if not self.null_hypothesis.strip() or not self.alternative_hypothesis.strip():
            raise ValueError("Interpretation hypotheses cannot be empty.")
        optional_messages = (
            self.question,
            self.decision,
            self.effect,
            self.uncertainty,
            self.practical_significance,
            self.warning_context,
        )
        if any(message is not None and not message.strip() for message in optional_messages):
            raise ValueError("Interpretation messages cannot be blank.")

    def to_dict(self) -> dict[str, str]:
        """Return populated interpretation fields as a JSON-compatible mapping."""
        values = {
            "question": self.question,
            "null_hypothesis": self.null_hypothesis,
            "alternative_hypothesis": self.alternative_hypothesis,
            "decision": self.decision,
            "effect": self.effect,
            "uncertainty": self.uncertainty,
            "practical_significance": self.practical_significance,
            "warning_context": self.warning_context,
        }
        return {key: value for key, value in values.items() if value is not None}

    def __getitem__(self, key: str) -> str:
        """Preserve read access used by the former interpretation mapping."""
        return self.to_dict()[key]

    @classmethod
    def from_dict(cls, values: dict[str, str]) -> "StatisticalInterpretation":
        """Convert the legacy hypothesis mapping to the structured contract."""
        return cls(
            null_hypothesis=values["null_hypothesis"],
            alternative_hypothesis=values["alternative_hypothesis"],
            question=values.get("question"),
            decision=values.get("decision"),
            effect=values.get("effect"),
            uncertainty=values.get("uncertainty"),
            practical_significance=values.get("practical_significance"),
            warning_context=values.get("warning_context"),
        )


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

    interpretation: StatisticalInterpretation | dict[str, str] = field(default_factory=dict)
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

        if isinstance(self.interpretation, dict) and {
            "null_hypothesis",
            "alternative_hypothesis",
        }.issubset(self.interpretation):
            object.__setattr__(
                self,
                "interpretation",
                StatisticalInterpretation.from_dict(self.interpretation),
            )

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
            "interpretation": (
                self.interpretation.to_dict()
                if isinstance(self.interpretation, StatisticalInterpretation)
                else dict(self.interpretation)
            ),
            "metadata": dict(self.metadata),
        }
