"""Safe in-memory CSV parsing and preview services."""

import csv
import json
import os
import re
from io import StringIO
from pathlib import PurePath

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from pandas.errors import EmptyDataError, ParserError

from app.errors import DatasetUploadError
from app.schemas.datasets import CSVColumnPreview, CSVPreviewResponse

DEFAULT_MAX_CSV_BYTES = 5 * 1024 * 1024
PREVIEW_ROW_LIMIT = 10
ALLOWED_DELIMITERS = (",", ";", "\t", "|")
ALLOWED_CONTENT_TYPES = {
    "application/csv",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "text/csv",
    "text/plain",
}


def get_max_csv_bytes() -> int:
    """Return the configured positive CSV upload limit in bytes."""
    raw_value = os.getenv("EXPERIMENTOS_MAX_CSV_BYTES")
    if raw_value is None:
        return DEFAULT_MAX_CSV_BYTES

    try:
        configured = int(raw_value)
    except ValueError:
        return DEFAULT_MAX_CSV_BYTES
    return configured if configured > 0 else DEFAULT_MAX_CSV_BYTES


def sanitize_csv_filename(filename: str | None) -> str:
    """Return a basename-only, display-safe CSV filename or raise a safe error."""
    basename = PurePath((filename or "").replace("\\", "/")).name.strip()
    sanitized = re.sub(r"[^A-Za-z0-9._ -]", "_", basename).strip(" .")
    if not sanitized:
        raise DatasetUploadError(
            "INVALID_FILENAME",
            "The uploaded file must have a valid filename.",
        )
    if not sanitized.lower().endswith(".csv"):
        raise DatasetUploadError(
            "INVALID_FILE_TYPE",
            "Only files with a .csv extension are supported.",
            details={"filename": sanitized},
        )
    return sanitized


def _validate_content_type(content_type: str | None) -> None:
    """Reject content types that are not compatible with CSV uploads."""
    normalized = (content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if normalized not in ALLOWED_CONTENT_TYPES:
        raise DatasetUploadError(
            "INVALID_FILE_TYPE",
            "The uploaded content type is not supported for CSV preview.",
            details={"content_type": normalized or None},
        )


def _normalize_delimiter(text: str, requested: str | None) -> str:
    """Validate an explicit delimiter or detect one from CSV text."""
    if requested is not None:
        if requested not in ALLOWED_DELIMITERS:
            raise DatasetUploadError(
                "INVALID_DELIMITER",
                "The delimiter must be one of comma, semicolon, tab, or pipe.",
                details={"delimiter": requested},
            )
        return requested

    try:
        return csv.Sniffer().sniff(text[:8192], delimiters="".join(ALLOWED_DELIMITERS)).delimiter
    except csv.Error as error:
        raise DatasetUploadError(
            "DELIMITER_DETECTION_FAILED",
            "The CSV delimiter could not be detected safely.",
        ) from error


def _validate_header(text: str, delimiter: str) -> None:
    """Reject missing, blank, or duplicate CSV column names."""
    try:
        header = next(csv.reader(StringIO(text), delimiter=delimiter))
    except (csv.Error, StopIteration) as error:
        raise DatasetUploadError(
            "INVALID_CSV",
            "The CSV file does not contain a readable header row.",
        ) from error

    normalized = [name.strip() for name in header]
    if not normalized or any(not name for name in normalized):
        raise DatasetUploadError(
            "MISSING_COLUMNS",
            "Every CSV column must have a non-empty name.",
        )
    if len(set(normalized)) != len(normalized):
        raise DatasetUploadError(
            "DUPLICATE_COLUMNS",
            "CSV column names must be unique.",
            details={"columns": normalized},
        )


def _infer_column_type(series: pd.Series) -> str:
    """Map a pandas series to a stable preview type."""
    non_missing = series.dropna()
    if is_bool_dtype(non_missing.dtype):
        return "boolean"
    if is_numeric_dtype(non_missing.dtype):
        numeric = non_missing.astype(float)
        return "integer" if ((numeric % 1) == 0).all() else "number"
    return "string"


def parse_csv_preview(
    content: bytes,
    *,
    filename: str | None,
    content_type: str | None,
    delimiter: str | None = None,
    max_bytes: int | None = None,
) -> CSVPreviewResponse:
    """Validate and parse CSV bytes into a safe, JSON-compatible preview."""
    safe_filename = sanitize_csv_filename(filename)
    _validate_content_type(content_type)
    effective_limit = max_bytes if max_bytes is not None else get_max_csv_bytes()
    size_bytes = len(content)
    if size_bytes > effective_limit:
        raise DatasetUploadError(
            "FILE_TOO_LARGE",
            "The uploaded CSV exceeds the configured size limit.",
            details={"size_bytes": size_bytes, "max_bytes": effective_limit},
            status_code=413,
        )
    if size_bytes == 0:
        raise DatasetUploadError("EMPTY_FILE", "The uploaded CSV is empty.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DatasetUploadError(
            "INVALID_ENCODING",
            "The uploaded CSV must use UTF-8 encoding.",
        ) from error

    selected_delimiter = _normalize_delimiter(text, delimiter)
    _validate_header(text, selected_delimiter)
    try:
        dataframe = pd.read_csv(StringIO(text), sep=selected_delimiter)
    except (EmptyDataError, ParserError, UnicodeError) as error:
        raise DatasetUploadError(
            "INVALID_CSV",
            "The uploaded file could not be parsed as a valid CSV.",
        ) from error

    if dataframe.empty:
        raise DatasetUploadError(
            "EMPTY_DATASET",
            "The uploaded CSV must contain at least one data row.",
        )

    columns = [
        CSVColumnPreview(
            name=str(name),
            inferred_type=_infer_column_type(dataframe[name]),
            missing_count=int(dataframe[name].isna().sum()),
        )
        for name in dataframe.columns
    ]
    preview_rows = json.loads(
        dataframe.head(PREVIEW_ROW_LIMIT).to_json(orient="records", date_format="iso")
    )

    return CSVPreviewResponse(
        filename=safe_filename,
        size_bytes=size_bytes,
        delimiter=selected_delimiter,
        row_count=int(dataframe.shape[0]),
        columns=columns,
        preview_rows=preview_rows,
    )
