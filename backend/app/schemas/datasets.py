"""Dataset upload and preview API schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class CSVColumnPreview(BaseModel):
    """Inferred metadata for one uploaded CSV column."""

    name: str
    inferred_type: Literal["boolean", "integer", "number", "string"]
    missing_count: int = Field(ge=0)


class CSVPreviewResponse(BaseModel):
    """Safe in-memory preview of an uploaded CSV file."""

    filename: str
    size_bytes: int = Field(ge=1)
    delimiter: str
    row_count: int = Field(ge=1)
    columns: list[CSVColumnPreview]
    preview_rows: list[dict[str, Any]]


class NormalizedDatasetResponse(BaseModel):
    """Normalized in-memory A/B dataset produced from a mapped CSV."""

    metric_type: Literal["binary", "continuous"]
    group_a: list[float]
    group_b: list[float]
    metadata: dict[str, Any]
