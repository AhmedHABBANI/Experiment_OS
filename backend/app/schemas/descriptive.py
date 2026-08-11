"""Descriptive-statistics API schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BinaryDescriptiveRequest(BaseModel):
    """Request body for binary A/B descriptive statistics."""

    group_a: list[float | None] = Field(min_length=1)
    group_b: list[float | None] = Field(min_length=1)
    confidence_level: float = Field(default=0.95, gt=0, lt=1)
    missing_policy: Literal["drop", "raise"] = "drop"


class ContinuousDescriptiveRequest(BaseModel):
    """Request body for continuous A/B descriptive statistics."""

    group_a: list[float | None] = Field(min_length=1)
    group_b: list[float | None] = Field(min_length=1)
    missing_policy: Literal["drop", "raise"] = "drop"


class DescriptiveResponse(BaseModel):
    """Standard descriptive-statistics response returned by the API."""

    model_config = ConfigDict(protected_namespaces=())

    metric_type: Literal["binary", "continuous"]
    group_a: dict[str, Any]
    group_b: dict[str, Any]
    comparison: dict[str, Any]
