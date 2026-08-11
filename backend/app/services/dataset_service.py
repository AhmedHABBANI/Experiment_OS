"""Safe in-memory CSV parsing and preview services."""

import csv
import json
import os
import re
from dataclasses import dataclass
from io import StringIO
from math import isfinite
from pathlib import PurePath
from typing import Any

import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from pandas.errors import EmptyDataError, ParserError

from app.errors import DatasetUploadError
from app.schemas.datasets import (
    CSVColumnPreview,
    CSVPreviewResponse,
    NormalizedDatasetResponse,
)
from experiment_os_stats import DataSource, MetricType, validate_ab_samples

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


@dataclass(frozen=True, slots=True)
class ParsedCSV:
    """Validated CSV content retained only for the current request."""

    filename: str
    size_bytes: int
    delimiter: str
    dataframe: pd.DataFrame


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


def _parse_csv(
    content: bytes,
    *,
    filename: str | None,
    content_type: str | None,
    delimiter: str | None,
    max_bytes: int | None,
) -> ParsedCSV:
    """Validate CSV bytes and return an in-memory dataframe."""
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
    dataframe.columns = [str(name).strip() for name in dataframe.columns]
    return ParsedCSV(
        filename=safe_filename,
        size_bytes=size_bytes,
        delimiter=selected_delimiter,
        dataframe=dataframe,
    )


def parse_csv_preview(
    content: bytes,
    *,
    filename: str | None,
    content_type: str | None,
    delimiter: str | None = None,
    max_bytes: int | None = None,
) -> CSVPreviewResponse:
    """Validate and parse CSV bytes into a safe, JSON-compatible preview."""
    parsed = _parse_csv(
        content,
        filename=filename,
        content_type=content_type,
        delimiter=delimiter,
        max_bytes=max_bytes,
    )
    dataframe = parsed.dataframe

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
        filename=parsed.filename,
        size_bytes=parsed.size_bytes,
        delimiter=parsed.delimiter,
        row_count=int(dataframe.shape[0]),
        columns=columns,
        preview_rows=preview_rows,
    )


def _value_token(value: Any) -> str | None:
    """Normalize a CSV scalar for stable manual modality matching."""
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else format(value, ".15g")
    token = str(value).strip()
    return token or None


def _validate_mapping_columns(
    dataframe: pd.DataFrame,
    *,
    group_column: str,
    metric_column: str,
) -> tuple[str, str]:
    """Validate and normalize selected group and metric column names."""
    normalized_group_column = group_column.strip()
    normalized_metric_column = metric_column.strip()
    missing = [
        name
        for name in (normalized_group_column, normalized_metric_column)
        if name not in dataframe.columns
    ]
    if missing:
        raise DatasetUploadError(
            "MISSING_COLUMNS",
            "One or more mapped CSV columns do not exist.",
            details={"missing_columns": missing, "available_columns": list(dataframe.columns)},
        )
    if normalized_group_column == normalized_metric_column:
        raise DatasetUploadError(
            "INVALID_MAPPING",
            "The group and metric columns must be different.",
        )
    return normalized_group_column, normalized_metric_column


def _normalize_metric_type(metric_type: str) -> MetricType:
    """Normalize a mapped metric type or raise a safe dataset error."""
    try:
        return MetricType(metric_type)
    except ValueError as error:
        raise DatasetUploadError(
            "INVALID_METRIC_TYPE",
            "The metric type must be binary or continuous.",
            details={"metric_type": metric_type},
        ) from error


def normalize_csv_dataset(
    content: bytes,
    *,
    filename: str | None,
    content_type: str | None,
    group_column: str,
    group_a_value: str,
    group_b_value: str,
    metric_column: str,
    metric_type: str,
    binary_success_value: str | None = None,
    binary_failure_value: str | None = None,
    delimiter: str | None = None,
    max_bytes: int | None = None,
) -> NormalizedDatasetResponse:
    """Map an uploaded CSV to validated in-memory A/B metric arrays."""
    parsed = _parse_csv(
        content,
        filename=filename,
        content_type=content_type,
        delimiter=delimiter,
        max_bytes=max_bytes,
    )
    dataframe = parsed.dataframe
    selected_group_column, selected_metric_column = _validate_mapping_columns(
        dataframe,
        group_column=group_column,
        metric_column=metric_column,
    )
    normalized_metric_type = _normalize_metric_type(metric_type)
    group_a_token = _value_token(group_a_value)
    group_b_token = _value_token(group_b_value)
    if group_a_token is None or group_b_token is None or group_a_token == group_b_token:
        raise DatasetUploadError(
            "INVALID_GROUP_MAPPING",
            "Group A and B values must be distinct and non-empty.",
        )

    success_token: str | None = None
    failure_token: str | None = None
    if normalized_metric_type is MetricType.BINARY:
        success_token = _value_token(binary_success_value)
        failure_token = _value_token(binary_failure_value)
        if success_token is None or failure_token is None or success_token == failure_token:
            raise DatasetUploadError(
                "INVALID_BINARY_MAPPING",
                "Binary success and failure values must be distinct and non-empty.",
            )
        success_token = success_token.casefold()
        failure_token = failure_token.casefold()

    group_a: list[float] = []
    group_b: list[float] = []
    exclusions = {
        "missing_group": 0,
        "unmapped_group": 0,
        "missing_metric": 0,
        "invalid_metric": 0,
    }
    for group_value, metric_value in zip(
        dataframe[selected_group_column],
        dataframe[selected_metric_column],
        strict=True,
    ):
        group_token = _value_token(group_value)
        if group_token is None:
            exclusions["missing_group"] += 1
            continue
        if group_token not in (group_a_token, group_b_token):
            exclusions["unmapped_group"] += 1
            continue

        metric_token = _value_token(metric_value)
        if metric_token is None:
            exclusions["missing_metric"] += 1
            continue
        if normalized_metric_type is MetricType.BINARY:
            binary_token = metric_token.casefold()
            if binary_token == success_token:
                normalized_value = 1.0
            elif binary_token == failure_token:
                normalized_value = 0.0
            else:
                exclusions["invalid_metric"] += 1
                continue
        else:
            if isinstance(metric_value, bool):
                exclusions["invalid_metric"] += 1
                continue
            try:
                normalized_value = float(metric_value)
            except (TypeError, ValueError):
                exclusions["invalid_metric"] += 1
                continue
            if not isfinite(normalized_value):
                exclusions["invalid_metric"] += 1
                continue

        target = group_a if group_token == group_a_token else group_b
        target.append(normalized_value)

    if not group_a or not group_b:
        raise DatasetUploadError(
            "INSUFFICIENT_GROUP_DATA",
            "Both mapped groups must retain at least one valid metric observation.",
            details={"retained_a": len(group_a), "retained_b": len(group_b)},
        )

    validated = validate_ab_samples(
        group_a,
        group_b,
        metric_type=normalized_metric_type,
        minimum_size=1,
    )
    normalized_a = [float(value) for value in validated.group_a.values]
    normalized_b = [float(value) for value in validated.group_b.values]
    excluded_rows = sum(exclusions.values())

    return NormalizedDatasetResponse(
        metric_type=normalized_metric_type.value,
        group_a=normalized_a,
        group_b=normalized_b,
        metadata={
            "source": DataSource.CSV_IMPORT.value,
            "filename": parsed.filename,
            "delimiter": parsed.delimiter,
            "original_rows": int(dataframe.shape[0]),
            "retained_rows": len(normalized_a) + len(normalized_b),
            "excluded_rows": excluded_rows,
            "exclusion_reasons": exclusions,
            "mapping": {
                "group_column": selected_group_column,
                "group_a_value": group_a_token,
                "group_b_value": group_b_token,
                "metric_column": selected_metric_column,
                "metric_type": normalized_metric_type.value,
                "binary_success_value": success_token,
                "binary_failure_value": failure_token,
            },
            "validation": {
                "group_a": validated.group_a.summary.to_dict(),
                "group_b": validated.group_b.summary.to_dict(),
            },
        },
    )
