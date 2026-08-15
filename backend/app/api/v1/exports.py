"""Report export endpoints."""

from fastapi import APIRouter, Response

from app.schemas.exports import AnalyzedDataCsvRequest, JsonExportRequest, JsonExportResponse
from app.services.export_service import (
    build_analyzed_data_csv,
    build_json_export,
    build_pdf_report,
    build_results_csv,
)

router = APIRouter()
reports_router = APIRouter()


@router.post("/json", response_model=JsonExportResponse)
def export_json(request: JsonExportRequest, response: Response) -> JsonExportResponse:
    """Return a downloadable, self-contained JSON experiment report."""
    response.headers["Content-Disposition"] = 'attachment; filename="experiment-os-report.json"'
    return build_json_export(request)


@router.post("/csv")
def export_results_csv(request: JsonExportRequest) -> Response:
    """Return flattened report results as a downloadable CSV artifact."""
    return Response(
        content=build_results_csv(request),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="experiment-os-results.csv"'},
    )


@router.post("/csv/data")
def export_analyzed_data_csv(request: AnalyzedDataCsvRequest) -> Response:
    """Return retained normalized observations as a downloadable CSV artifact."""
    return Response(
        content=build_analyzed_data_csv(request),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="experiment-os-analyzed-data.csv"'},
    )


@reports_router.post("/pdf")
def export_pdf_report(request: JsonExportRequest) -> Response:
    """Return a complete in-memory experiment report as a downloadable PDF."""
    return Response(
        content=build_pdf_report(request),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="experiment-os-report.pdf"'},
    )
