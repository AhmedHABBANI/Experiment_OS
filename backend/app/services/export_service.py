"""In-memory report export assembly."""

import csv
import json
from datetime import UTC, datetime
from html import escape
from io import BytesIO, StringIO
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.exports import AnalyzedDataCsvRequest, JsonExportRequest, JsonExportResponse


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


def build_analyzed_data_csv(request: AnalyzedDataCsvRequest) -> str:
    """Serialize retained normalized A/B observations in a stable long format."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("group", "observation", "value"))
    for group, values in (("A", request.dataset.group_a), ("B", request.dataset.group_b)):
        retained_values = (value for value in values if value is not None)
        for observation, value in enumerate(retained_values, start=1):
            writer.writerow((group, observation, value))
    return output.getvalue()


def build_pdf_report(request: JsonExportRequest) -> bytes:
    """Build a paginated PDF report from the authoritative experiment state."""
    report = build_json_export(request).model_dump(mode="json")
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="ExperimentOS experiment report",
        author="ExperimentOS",
    )
    styles = _pdf_styles()
    story: list[Any] = [
        Paragraph("ExperimentOS experiment report", styles["Title"]),
        Paragraph(
            f"Generated {escape(report['exported_at'])} | Source: {escape(report['source'])}",
            styles["Meta"],
        ),
        Spacer(1, 5 * mm),
    ]
    story.extend(_pdf_section("Configuration", report["configuration"], styles))
    story.extend(_pdf_group_summary(report["descriptive_summary"], styles))
    story.extend(_pdf_comparison_chart(report["descriptive_summary"], styles))
    story.extend(_pdf_analysis(report["analysis_result"], styles))
    story.extend(
        _pdf_section("Interpretation", report["analysis_result"]["interpretation"], styles)
    )
    story.extend(_pdf_warnings(report["analysis_result"]["warnings"], styles))
    reproducibility = {
        "application": report["application"],
        "schema_version": report["schema_version"],
        "dataset_metadata": report["dataset"]["metadata"],
        "analysis_metadata": report["analysis_result"]["metadata"],
    }
    story.extend(_pdf_section("Reproducibility", reproducibility, styles))
    document.build(story)
    return output.getvalue()


def _pdf_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#17324D"),
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "Heading": ParagraphStyle(
            "ReportHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#17324D"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "Body": ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=8, leading=11),
        "Meta": ParagraphStyle(
            "ReportMeta",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#51606F"),
            alignment=TA_CENTER,
        ),
    }


def _pdf_section(
    title: str, values: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> list[Any]:
    rows = [["Field", "Value"]]
    rows.extend(
        [escape(field), Paragraph(escape(_display_value(value)), styles["Body"])]
        for field, value in _flatten_report(values)
        if not _is_large_distribution(field, value)
    )
    return [Paragraph(title, styles["Heading"]), _pdf_table(rows)]


def _pdf_group_summary(summary: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    fields = list(dict.fromkeys((*summary["group_a"].keys(), *summary["group_b"].keys())))
    rows = [["Metric", "Group A", "Group B"]]
    rows.extend(
        [
            escape(field),
            escape(_display_value(summary["group_a"].get(field))),
            escape(_display_value(summary["group_b"].get(field))),
        ]
        for field in fields
    )
    comparison_rows = [["Comparison", "Value"]]
    comparison_rows.extend(
        [escape(field), escape(_display_value(value))]
        for field, value in summary["comparison"].items()
    )
    return [
        Paragraph("Group summary", styles["Heading"]),
        _pdf_table(rows),
        Spacer(1, 3 * mm),
        _pdf_table(comparison_rows),
    ]


def _pdf_comparison_chart(summary: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    metric = "proportion" if summary["metric_type"] == "binary" else "mean"
    values = [summary["group_a"].get(metric), summary["group_b"].get(metric)]
    if not all(isinstance(value, int | float) for value in values):
        return []
    drawing = Drawing(150 * mm, 58 * mm)
    chart = VerticalBarChart()
    chart.x = 20 * mm
    chart.y = 8 * mm
    chart.width = 115 * mm
    chart.height = 42 * mm
    chart.data = [values]
    chart.categoryAxis.categoryNames = ["Group A", "Group B"]
    chart.valueAxis.valueMin = min(0, min(values))
    chart.valueAxis.valueMax = max(values) if max(values) > 0 else 1
    chart.bars[0].fillColor = colors.HexColor("#2F6B7C")
    chart.valueAxis.labelTextFormat = "%0.4g"
    drawing.add(chart)
    return [KeepTogether([Paragraph(f"Group comparison ({metric})", styles["Heading"]), drawing])]


def _pdf_analysis(result: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    result_fields = {
        key: value
        for key, value in result.items()
        if key not in {"assumptions", "warnings", "interpretation", "metadata"}
    }
    elements = _pdf_section("Statistical analysis", result_fields, styles)
    assumptions = result["assumptions"] or ["No additional assumptions were reported."]
    elements.extend(
        [
            Paragraph("Assumptions", styles["Heading"]),
            *[Paragraph(f"- {escape(item)}", styles["Body"]) for item in assumptions],
        ]
    )
    return elements


def _pdf_warnings(warnings: list[dict[str, Any]], styles: dict[str, ParagraphStyle]) -> list[Any]:
    if not warnings:
        content = [Paragraph("No statistical warnings were reported.", styles["Body"])]
    else:
        content = [
            Paragraph(
                f"{escape(warning['severity'].upper())} | {escape(warning['code'])}: "
                f"{escape(warning['message'])}",
                styles["Body"],
            )
            for warning in warnings
        ]
    return [Paragraph("Warnings", styles["Heading"]), *content]


def _pdf_table(rows: list[list[Any]]) -> Table:
    table = Table(rows, colWidths=None, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE7EA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17324D")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#AAB7C0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F8")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _display_value(value: Any) -> str:
    if value is None:
        return "Not applicable"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list | dict):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return str(value)


def _is_large_distribution(field: str, value: Any) -> bool:
    return "distribution" in field and isinstance(value, list) and len(value) > 20


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
