"""Typed export contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.analyses import StatisticalAnalysisResponse
from app.schemas.descriptive import DescriptiveResponse
from app.schemas.simulations import SimulationResponse


class AnalyzedDataCsvRequest(BaseModel):
    """Normalized in-memory dataset required for an analyzed-data CSV export."""

    dataset: SimulationResponse


class JsonExportRequest(BaseModel):
    """Complete in-memory experiment state required for a JSON export."""

    source: Literal["simulation", "csv_import"]
    configuration: dict[str, Any]
    dataset: SimulationResponse
    descriptive_summary: DescriptiveResponse
    analysis_result: StatisticalAnalysisResponse


class JsonExportResponse(BaseModel):
    """Versioned, self-contained ExperimentOS JSON report."""

    model_config = ConfigDict(protected_namespaces=())

    schema_version: Literal["1.0"]
    application: dict[str, str]
    exported_at: datetime
    source: Literal["simulation", "csv_import"]
    configuration: dict[str, Any]
    dataset: SimulationResponse
    descriptive_summary: DescriptiveResponse
    analysis_result: StatisticalAnalysisResponse
