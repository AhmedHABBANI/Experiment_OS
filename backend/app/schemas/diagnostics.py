"""Diagnostic-visualization API schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class BinaryDiagnosticsRequest(BaseModel):
    """Request body for binary rate visualization data."""

    group_a: list[float | None] = Field(min_length=1)
    group_b: list[float | None] = Field(min_length=1)
    confidence_level: float = Field(default=0.95, gt=0, lt=1)
    missing_policy: Literal["drop", "raise"] = "drop"


class BinaryDiagnosticsResponse(BaseModel):
    """Binary rates and confidence intervals ready for plotting."""

    groups: list[str]
    proportions: list[float]
    ci_lower: list[float]
    ci_upper: list[float]
    counts: list[int]
    successes: list[int]


class ContinuousDiagnosticsRequest(BaseModel):
    """Request body for continuous distribution visualization data."""

    group_a: list[float | None] = Field(min_length=1)
    group_b: list[float | None] = Field(min_length=1)
    bins: int = Field(default=10, ge=1)
    missing_policy: Literal["drop", "raise"] = "drop"


class HistogramResponse(BaseModel):
    """Histogram bin edges and counts for one group."""

    bin_edges: list[float]
    counts: list[int]


class BoxplotResponse(BaseModel):
    """Five-number boxplot summary for one group."""

    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float


class QQPlotResponse(BaseModel):
    """Normal QQ plot coordinates for one group."""

    theoretical_quantiles: list[float]
    sample_quantiles: list[float]


class ContinuousDiagnosticsResponse(BaseModel):
    """Continuous histogram, boxplot and QQ plot data."""

    histograms: dict[str, HistogramResponse]
    boxplots: dict[str, BoxplotResponse]
    qq_plots: dict[str, QQPlotResponse]
