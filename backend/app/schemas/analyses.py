"""Statistical-analysis API schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BinaryAnalysisRequest(BaseModel):
    """Request body shared by independent binary A/B tests."""

    group_a: list[float | None] = Field(min_length=1)
    group_b: list[float | None] = Field(min_length=1)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    alternative: Literal["two-sided", "greater", "less"] = "two-sided"
    missing_policy: Literal["drop", "raise"] = "drop"


class ContinuousAnalysisRequest(BaseModel):
    """Request body shared by independent continuous A/B tests."""

    group_a: list[float | None] = Field(min_length=2)
    group_b: list[float | None] = Field(min_length=2)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    alternative: Literal["two-sided", "greater", "less"] = "two-sided"
    missing_policy: Literal["drop", "raise"] = "drop"


class ConfidenceIntervalResponse(BaseModel):
    """Confidence interval returned by an analysis when applicable."""

    lower: float
    upper: float
    level: float
    parameter: str | None
    method: str | None


class StatisticalWarningResponse(BaseModel):
    """Structured statistical warning returned by an analysis."""

    code: str
    message: str
    severity: Literal["info", "warning", "error"]
    details: dict[str, Any]


class StatisticalAnalysisResponse(BaseModel):
    """Shared HTTP representation of a statistical result."""

    model_config = ConfigDict(protected_namespaces=())

    test_name: str
    metric_type: Literal["binary", "continuous"]
    statistic: float | None
    p_value: float | None
    alpha: float
    alternative: Literal["two-sided", "greater", "less"]
    estimate: float | None
    confidence_interval: ConfidenceIntervalResponse | None
    effect_size: float | None
    effect_size_name: str | None
    reject_null: bool | None
    assumptions: list[str]
    warnings: list[StatisticalWarningResponse]
    interpretation: dict[str, str]
    metadata: dict[str, Any]
