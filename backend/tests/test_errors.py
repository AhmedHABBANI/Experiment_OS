"""Tests for safe API handling of unexpected failures."""

import logging

from fastapi.testclient import TestClient

from app.main import create_app


def test_unexpected_error_is_logged_and_returns_safe_payload(caplog) -> None:
    app = create_app()

    @app.get("/test/unexpected-error")
    def raise_unexpected_error() -> None:
        raise RuntimeError("private implementation detail")

    client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="app.errors"):
        response = client.get("/test/unexpected-error")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected internal error occurred.",
            "details": {},
        }
    }
    assert "private implementation detail" not in response.text
    assert "Unhandled API error on GET /test/unexpected-error" in caplog.text
