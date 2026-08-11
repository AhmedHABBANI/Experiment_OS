"""Tests for simulation API routes."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_binary_simulation_endpoint_returns_simulated_dataset() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/simulations/binary",
        json={
            "n_a": 3,
            "n_b": 2,
            "p_a": 0.5,
            "p_b": 0.75,
            "seed": 42,
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["metric_type"] == "binary"
    assert len(payload["group_a"]) == 3
    assert len(payload["group_b"]) == 2
    assert payload["metadata"]["seed"] == 42


def test_continuous_simulation_endpoint_returns_simulated_dataset() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/simulations/continuous",
        json={
            "n_a": 4,
            "n_b": 5,
            "mean_a": 10.0,
            "mean_b": 12.0,
            "std_a": 2.0,
            "std_b": 3.0,
            "distribution": "normal",
            "seed": 7,
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["metric_type"] == "continuous"
    assert len(payload["group_a"]) == 4
    assert len(payload["group_b"]) == 5
    assert payload["metadata"]["distribution"] == "normal"


def test_simulation_endpoint_returns_validation_errors() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/simulations/binary",
        json={
            "n_a": 0,
            "n_b": 2,
            "p_a": 0.5,
            "p_b": 0.75,
        },
    )

    assert response.status_code == 422
