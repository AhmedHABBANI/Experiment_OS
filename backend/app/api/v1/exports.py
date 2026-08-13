"""Report export endpoints."""

from fastapi import APIRouter, Response

from app.schemas.exports import JsonExportRequest, JsonExportResponse
from app.services.export_service import build_json_export

router = APIRouter()


@router.post("/json", response_model=JsonExportResponse)
def export_json(request: JsonExportRequest, response: Response) -> JsonExportResponse:
    """Return a downloadable, self-contained JSON experiment report."""
    response.headers["Content-Disposition"] = 'attachment; filename="experiment-os-report.json"'
    return build_json_export(request)
