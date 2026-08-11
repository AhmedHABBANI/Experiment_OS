"""Tests for diagnostic-visualization API routes."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_binary_diagnostics_endpoint_returns_plot_data() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/diagnostics/binary-rate",
        json={
            "group_a": [1, 0, 1, None],
            "group_b": [1, 1, 0, 0],
            "confidence_level": 0.95,
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["groups"] == ["A", "B"]
    assert payload["counts"] == [3, 4]
    assert payload["successes"] == [2, 2]
    assert payload["proportions"] == [2 / 3, 0.5]
    assert len(payload["ci_lower"]) == 2
    assert len(payload["ci_upper"]) == 2


def test_continuous_diagnostics_endpoint_returns_all_plot_types() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/diagnostics/continuous-distribution",
        json={
            "group_a": [1.0, 2.0, 3.0, None],
            "group_b": [2.0, 4.0, 6.0],
            "bins": 2,
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["histograms"]["A"]["counts"] == [1, 2]
    assert len(payload["histograms"]["A"]["bin_edges"]) == 3
    assert payload["boxplots"]["A"]["median"] == 2.0
    assert payload["boxplots"]["B"]["maximum"] == 6.0
    assert payload["qq_plots"]["A"]["sample_quantiles"] == [1.0, 2.0, 3.0]
    assert len(payload["qq_plots"]["B"]["theoretical_quantiles"]) == 3


def test_diagnostics_endpoint_returns_domain_error_for_invalid_binary_values() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/diagnostics/binary-rate",
        json={"group_a": [0, 2], "group_b": [0, 1]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATA_VALIDATION_ERROR"


def test_diagnostics_endpoint_can_reject_missing_values() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/diagnostics/continuous-distribution",
        json={
            "group_a": [1.0, None, 3.0],
            "group_b": [2.0, 4.0],
            "missing_policy": "raise",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["details"]["missing_policy"] == "raise"


def test_diagnostics_endpoint_rejects_invalid_bin_count() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/diagnostics/continuous-distribution",
        json={"group_a": [1.0], "group_b": [2.0], "bins": 0},
    )

    assert response.status_code == 422
