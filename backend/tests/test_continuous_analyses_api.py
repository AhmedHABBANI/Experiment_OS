"""Tests for continuous statistical-analysis API routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_student_t_endpoint_returns_shared_result() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/student-t",
        json={
            "group_a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "group_b": [4.0, 5.0, 6.0, 7.0, 8.0],
            "alpha": 0.05,
            "alternative": "greater",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["test_name"] == "student_t_test"
    assert payload["metric_type"] == "continuous"
    assert payload["alternative"] == "greater"
    assert payload["estimate"] == pytest.approx(3.0)
    assert payload["reject_null"] is True
    assert payload["confidence_interval"]["method"] == "student_t_pooled"
    assert payload["effect_size_name"] == "cohens_d"
    assert payload["metadata"]["difference_direction"] == "group_b_minus_group_a"
    assert payload["interpretation"]["decision"]


def test_welch_t_endpoint_returns_shared_result() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/welch-t",
        json={
            "group_a": [1.0, 2.0, 3.0, 4.0],
            "group_b": [5.0, 7.0, 9.0, 11.0, 13.0],
            "alpha": 0.05,
            "alternative": "greater",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["test_name"] == "welch_t_test"
    assert payload["metric_type"] == "continuous"
    assert payload["alternative"] == "greater"
    assert payload["estimate"] == pytest.approx(6.5)
    assert payload["reject_null"] is True
    assert payload["confidence_interval"]["method"] == "welch_t"
    assert payload["effect_size_name"] == "cohens_d"
    assert payload["metadata"]["degrees_of_freedom_method"] == "welch_satterthwaite"
    assert payload["metadata"]["difference_direction"] == "group_b_minus_group_a"


def test_welch_t_endpoint_returns_structured_degenerate_error() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/welch-t",
        json={"group_a": [1.0, 1.0], "group_b": [2.0, 2.0]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DEGENERATE_SAMPLE_ERROR"


def test_mann_whitney_endpoint_returns_rank_result_and_warnings() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/mann-whitney",
        json={
            "group_a": [1.0, 2.0, 3.0, 4.0],
            "group_b": [5.0, 6.0, 7.0, 8.0],
            "alpha": 0.05,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["test_name"] == "mann_whitney_u_test"
    assert payload["alternative"] == "two-sided"
    assert payload["estimate"] is None
    assert payload["effect_size"] == pytest.approx(1.0)
    assert payload["effect_size_name"] == "rank_biserial_correlation"
    assert payload["metadata"]["u_statistic_group"] == "group_b"
    assert payload["metadata"]["probability_of_superiority_b_over_a"] == pytest.approx(1.0)
    assert payload["warnings"][0]["code"] == "MANN_WHITNEY_NOT_MEDIAN_TEST"
    assert "rank distributions" in payload["interpretation"]["question"]


def test_mann_whitney_endpoint_supports_one_observation_per_group() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/mann-whitney",
        json={"group_a": [1.0], "group_b": [2.0]},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["n_a"] == 1


def test_mann_whitney_endpoint_returns_structured_degenerate_error() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/mann-whitney",
        json={"group_a": [1.0, 1.0], "group_b": [1.0, 1.0]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DEGENERATE_SAMPLE_ERROR"


def test_student_t_endpoint_returns_structured_degenerate_error() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/student-t",
        json={"group_a": [1.0, 1.0], "group_b": [2.0, 2.0]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DEGENERATE_SAMPLE_ERROR"


def test_student_t_endpoint_can_reject_missing_values() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/student-t",
        json={
            "group_a": [1.0, None, 2.0],
            "group_b": [2.0, 3.0, 4.0],
            "missing_policy": "raise",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATA_VALIDATION_ERROR"


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"group_a": [1.0], "group_b": [2.0, 3.0]},
        {"group_a": [1.0, 2.0], "group_b": [2.0, 3.0], "alpha": 0},
        {"group_a": [1.0, 2.0], "group_b": [2.0, 3.0], "alternative": "up"},
    ],
)
def test_student_t_endpoint_returns_schema_validation_errors(
    invalid_payload: dict[str, object],
) -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/analyses/student-t", json=invalid_payload)

    assert response.status_code == 422
