"""Contract tests for the CSV files published with the documentation."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

EXAMPLES_DIRECTORY = Path(__file__).parents[2] / "examples"


@pytest.mark.parametrize(
    ("filename", "mapping", "expected_a", "expected_b"),
    [
        (
            "binary_ab.csv",
            {
                "group_column": "variant",
                "group_a_value": "control",
                "group_b_value": "treatment",
                "metric_column": "converted",
                "metric_type": "binary",
                "binary_success_value": "yes",
                "binary_failure_value": "no",
            },
            [0.0, 1.0, 0.0, 1.0],
            [1.0, 0.0, 1.0, 1.0],
        ),
        (
            "continuous_ab.csv",
            {
                "group_column": "variant",
                "group_a_value": "control",
                "group_b_value": "treatment",
                "metric_column": "revenue",
                "metric_type": "continuous",
            },
            [42.5, 38.0, 51.25, 46.0],
            [49.0, 55.5, 47.75, 60.0],
        ),
    ],
)
def test_documented_csv_examples_preview_and_normalize(
    filename: str,
    mapping: dict[str, str],
    expected_a: list[float],
    expected_b: list[float],
) -> None:
    """Keep each published example aligned with the documented import mapping."""
    content = (EXAMPLES_DIRECTORY / filename).read_bytes()
    client = TestClient(create_app())
    upload = {"file": (filename, content, "text/csv")}

    preview = client.post("/api/v1/datasets/preview", files=upload)
    normalized = client.post("/api/v1/datasets/validate", files=upload, data=mapping)

    assert preview.status_code == 200
    assert preview.json()["row_count"] == 8
    assert normalized.status_code == 200
    assert normalized.json()["group_a"] == expected_a
    assert normalized.json()["group_b"] == expected_b
    assert normalized.json()["metadata"]["excluded_rows"] == 0
