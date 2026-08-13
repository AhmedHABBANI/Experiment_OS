"""In-memory report export assembly."""

from datetime import UTC, datetime

from app.schemas.exports import JsonExportRequest, JsonExportResponse


def build_json_export(request: JsonExportRequest) -> JsonExportResponse:
    """Build a versioned JSON report without altering statistical values."""
    return JsonExportResponse(
        schema_version="1.0",
        application={"name": "ExperimentOS", "version": "0.1.0"},
        exported_at=datetime.now(UTC),
        source=request.source,
        configuration=request.configuration,
        dataset=request.dataset,
        descriptive_summary=request.descriptive_summary,
        analysis_result=request.analysis_result,
    )
