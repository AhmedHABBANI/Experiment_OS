"""Dataset upload and preview endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.datasets import CSVPreviewResponse, NormalizedDatasetResponse
from app.services.dataset_service import (
    get_max_csv_bytes,
    normalize_csv_dataset,
    parse_csv_preview,
)

router = APIRouter()


async def _read_bounded_upload(file: UploadFile) -> tuple[bytes, int]:
    """Read at most the configured CSV limit plus one sentinel byte."""
    max_bytes = get_max_csv_bytes()
    return await file.read(max_bytes + 1), max_bytes


@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv_dataset(
    file: Annotated[UploadFile, File(description="UTF-8 CSV file")],
    delimiter: Annotated[str | None, Form()] = None,
) -> CSVPreviewResponse:
    """Validate an uploaded CSV and return an in-memory preview."""
    content, max_bytes = await _read_bounded_upload(file)
    return parse_csv_preview(
        content,
        filename=file.filename,
        content_type=file.content_type,
        delimiter=delimiter,
        max_bytes=max_bytes,
    )


@router.post("/validate", response_model=NormalizedDatasetResponse)
async def validate_csv_dataset(
    file: Annotated[UploadFile, File(description="UTF-8 CSV file")],
    group_column: Annotated[str, Form()],
    group_a_value: Annotated[str, Form()],
    group_b_value: Annotated[str, Form()],
    metric_column: Annotated[str, Form()],
    metric_type: Annotated[str, Form()],
    binary_success_value: Annotated[str | None, Form()] = None,
    binary_failure_value: Annotated[str | None, Form()] = None,
    delimiter: Annotated[str | None, Form()] = None,
) -> NormalizedDatasetResponse:
    """Map an uploaded CSV to a normalized, validated in-memory A/B dataset."""
    content, max_bytes = await _read_bounded_upload(file)
    return normalize_csv_dataset(
        content,
        filename=file.filename,
        content_type=file.content_type,
        group_column=group_column,
        group_a_value=group_a_value,
        group_b_value=group_b_value,
        metric_column=metric_column,
        metric_type=metric_type,
        binary_success_value=binary_success_value,
        binary_failure_value=binary_failure_value,
        delimiter=delimiter,
        max_bytes=max_bytes,
    )
