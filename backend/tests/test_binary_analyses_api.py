"""Tests for binary statistical-analysis API routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_two_proportion_z_endpoint_returns_shared_result() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/two-proportion-z",
        json={
            "group_a": [1] * 20 + [0] * 80,
            "group_b": [1] * 40 + [0] * 60,
            "alpha": 0.05,
            "alternative": "greater",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["test_name"] == "two_proportion_z_test"
    assert payload["metric_type"] == "binary"
    assert payload["alternative"] == "greater"
    assert payload["estimate"] == pytest.approx(0.2)
    assert payload["reject_null"] is True
    assert payload["confidence_interval"]["method"] == "wald_unpooled"
    assert payload["metadata"]["difference_direction"] == "group_b_minus_group_a"


def test_fisher_exact_endpoint_returns_shared_result() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/fisher-exact",
        json={
            "group_a": [1] * 2 + [0] * 18,
            "group_b": [1] * 12 + [0] * 8,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["test_name"] == "fisher_exact_test"
    assert payload["confidence_interval"] is None
    assert payload["effect_size_name"] == "odds_ratio"
    assert payload["metadata"]["contingency_table"] == [[12, 8], [2, 18]]
    assert payload["reject_null"] is True


def test_fisher_endpoint_serializes_non_finite_odds_ratio_safely() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/fisher-exact",
        json={
            "group_a": [0] * 10,
            "group_b": [1] * 3 + [0] * 7,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["statistic"] is None
    assert payload["effect_size"] is None
    assert payload["warnings"][0]["code"] == "NON_FINITE_ODDS_RATIO"


def test_analysis_endpoint_returns_structured_invalid_data_error() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/two-proportion-z",
        json={"group_a": [0, 2], "group_b": [0, 1]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATA_VALIDATION_ERROR"
    assert response.json()["error"]["details"]["sample_name"] == "group_a"


def test_analysis_endpoint_returns_structured_degenerate_error() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/fisher-exact",
        json={"group_a": [0, 0], "group_b": [0, 0]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DEGENERATE_SAMPLE_ERROR"


def test_analysis_endpoint_can_reject_missing_values() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/two-proportion-z",
        json={
            "group_a": [0, None, 1],
            "group_b": [0, 1, 1],
            "missing_policy": "raise",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["details"]["missing_policy"] == "raise"


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"group_a": [], "group_b": [0, 1]},
        {"group_a": [0, 1], "group_b": [0, 1], "alpha": 1},
        {"group_a": [0, 1], "group_b": [0, 1], "alternative": "up"},
    ],
)
def test_analysis_endpoint_returns_schema_validation_errors(
    invalid_payload: dict[str, object],
) -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/analyses/two-proportion-z",
        json=invalid_payload,
    )

    assert response.status_code == 422
