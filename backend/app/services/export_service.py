"""In-memory report export assembly."""

import csv
import json
from datetime import UTC, datetime
from io import StringIO
from typing import Any

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


def build_results_csv(request: JsonExportRequest) -> str:
    """Flatten the authoritative report payload into a stable field-value CSV."""
    report = build_json_export(request).model_dump(mode="json")
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in _flatten_report(report):
        writer.writerow((field, _csv_value(value)))
    return output.getvalue()


def _flatten_report(value: Any, *, prefix: str = "") -> list[tuple[str, Any]]:
    """Return deterministic dotted paths while preserving complex leaf values."""
    if not isinstance(value, dict):
        return [(prefix, value)]

    rows: list[tuple[str, Any]] = []
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(child, dict):
            rows.extend(_flatten_report(child, prefix=path))
        else:
            rows.append((path, child))
    return rows


def _csv_value(value: Any) -> str:
    """Serialize one flattened report value without losing structured arrays."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return str(value)
