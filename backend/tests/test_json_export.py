"""Tests for the versioned JSON export endpoint."""

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import create_app


def _export_request() -> dict[str, object]:
    analysis = {
        "test_name": "welch_t_test",
        "metric_type": "continuous",
        "statistic": 2.345678,
        "p_value": 0.019876,
        "alpha": 0.05,
        "alternative": "two-sided",
        "estimate": 1.25,
        "confidence_interval": {
            "lower": 0.2,
            "upper": 2.3,
            "level": 0.95,
            "parameter": "difference_in_means_b_minus_a",
            "method": "welch_t",
        },
        "effect_size": 0.42,
        "effect_size_name": "cohens_d",
        "reject_null": True,
        "assumptions": ["The groups are independent."],
        "warnings": [],
        "interpretation": {"decision": "Reject H0 at the selected alpha."},
        "metadata": {"degrees_of_freedom": 17.5, "seed": 42},
    }
    return {
        "source": "simulation",
        "configuration": {
            "simulation": {"distribution": "normal", "seed": 42},
            "analysis": {"test": "welch-t", "alpha": 0.05},
        },
        "dataset": {
            "metric_type": "continuous",
            "group_a": [1.0, 2.0, 3.0],
            "group_b": [2.0, 3.0, 4.0],
            "metadata": {"source": "simulation", "seed": 42},
        },
        "descriptive_summary": {
            "metric_type": "continuous",
            "group_a": {"n": 3, "mean": 2.0},
            "group_b": {"n": 3, "mean": 3.0},
            "comparison": {"mean_difference": 1.0},
        },
        "analysis_result": analysis,
    }


def test_json_export_preserves_complete_statistical_result() -> None:
    client = TestClient(create_app())
    request = _export_request()

    response = client.post("/api/v1/exports/json", json=request)
    payload = response.json()

    assert response.status_code == 200
    assert response.headers["content-disposition"] == (
        'attachment; filename="experiment-os-report.json"'
    )
    assert payload["schema_version"] == "1.0"
    assert payload["application"] == {"name": "ExperimentOS", "version": "0.1.0"}
    assert datetime.fromisoformat(payload["exported_at"]).tzinfo is not None
    assert payload["dataset"] == request["dataset"]
    assert payload["descriptive_summary"] == request["descriptive_summary"]
    assert payload["analysis_result"] == request["analysis_result"]


def test_json_export_rejects_incomplete_result() -> None:
    client = TestClient(create_app())
    request = _export_request()
    del request["analysis_result"]

    response = client.post("/api/v1/exports/json", json=request)

    assert response.status_code == 422
