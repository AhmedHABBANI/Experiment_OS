"""Tests for descriptive-statistics API routes."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_binary_descriptive_endpoint_returns_summary() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/descriptive/binary",
        json={
            "group_a": [1, 0, 1, None],
            "group_b": [1, 1, 1, 0],
            "confidence_level": 0.95,
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["metric_type"] == "binary"
    assert payload["group_a"]["n"] == 3
    assert payload["group_a"]["missing_count"] == 1
    assert payload["group_a"]["successes"] == 2
    assert payload["group_b"]["proportion"] == 0.75
    assert payload["comparison"]["absolute_difference"] == 0.75 - (2 / 3)


def test_continuous_descriptive_endpoint_returns_summary() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/descriptive/continuous",
        json={
            "group_a": [1.0, 2.0, 3.0, None],
            "group_b": [3.0, 4.0, 5.0],
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["metric_type"] == "continuous"
    assert payload["group_a"]["n"] == 3
    assert payload["group_a"]["missing_count"] == 1
    assert payload["group_a"]["mean"] == 2.0
    assert payload["group_b"]["median"] == 4.0
    assert payload["comparison"]["mean_difference"] == 2.0


def test_descriptive_endpoint_returns_domain_error_for_invalid_binary_values() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/descriptive/binary",
        json={
            "group_a": [1, 2, 0],
            "group_b": [1, 0, 1],
        },
    )

    payload = response.json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "DATA_VALIDATION_ERROR"
    assert payload["error"]["details"]["sample_name"] == "group_a"


def test_descriptive_endpoint_can_reject_missing_values() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/descriptive/continuous",
        json={
            "group_a": [1.0, None, 3.0],
            "group_b": [2.0, 4.0, 6.0],
            "missing_policy": "raise",
        },
    )

    payload = response.json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "DATA_VALIDATION_ERROR"
    assert payload["error"]["details"]["missing_policy"] == "raise"


def test_descriptive_endpoint_returns_schema_validation_errors() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/descriptive/binary",
        json={
            "group_a": [],
            "group_b": [1, 0],
        },
    )

    assert response.status_code == 422
