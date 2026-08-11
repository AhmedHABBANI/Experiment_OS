"""Dataset upload and preview endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.datasets import CSVPreviewResponse
from app.services.dataset_service import get_max_csv_bytes, parse_csv_preview

router = APIRouter()


@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv_dataset(
    file: Annotated[UploadFile, File(description="UTF-8 CSV file")],
    delimiter: Annotated[str | None, Form()] = None,
) -> CSVPreviewResponse:
    """Validate an uploaded CSV and return an in-memory preview."""
    max_bytes = get_max_csv_bytes()
    content = await file.read(max_bytes + 1)
    return parse_csv_preview(
        content,
        filename=file.filename,
        content_type=file.content_type,
        delimiter=delimiter,
        max_bytes=max_bytes,
    )
