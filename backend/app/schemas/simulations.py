"""Simulation API schemas."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BinarySimulationRequest(BaseModel):
    """Request body for binary A/B simulation."""

    n_a: int = Field(ge=1)
    n_b: int = Field(ge=1)
    p_a: float = Field(ge=0, le=1)
    p_b: float = Field(ge=0, le=1)
    seed: int | None = None
    missing_rate: float = Field(default=0.0, ge=0, le=1)


class ContinuousSimulationRequest(BaseModel):
    """Request body for continuous A/B simulation."""

    n_a: int = Field(ge=1)
    n_b: int = Field(ge=1)
    mean_a: float
    mean_b: float
    std_a: float = Field(gt=0)
    std_b: float = Field(gt=0)
    distribution: Literal["normal", "exponential", "lognormal"] = "normal"
    seed: int | None = None
    missing_rate: float = Field(default=0.0, ge=0, le=1)
    outlier_rate: float = Field(default=0.0, ge=0, le=1)
    outlier_multiplier: float = Field(default=6.0, gt=0)


class SimulationResponse(BaseModel):
    """Normalized simulation response returned by the API."""

    model_config = ConfigDict(protected_namespaces=())

    metric_type: Literal["binary", "continuous"]
    group_a: list[float | None]
    group_b: list[float | None]
    metadata: dict[str, Any]
