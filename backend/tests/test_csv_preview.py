"""Tests for safe in-memory CSV preview uploads."""

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_csv_preview_returns_columns_types_missing_counts_and_rows() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={
            "file": (
                "experiment.csv",
                b"group,converted,revenue\nA,true,12.5\nB,false,\n",
                "text/csv",
            )
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["filename"] == "experiment.csv"
    assert payload["delimiter"] == ","
    assert payload["row_count"] == 2
    assert payload["columns"] == [
        {"name": "group", "inferred_type": "string", "missing_count": 0},
        {"name": "converted", "inferred_type": "boolean", "missing_count": 0},
        {"name": "revenue", "inferred_type": "number", "missing_count": 1},
    ]
    assert payload["preview_rows"][1]["revenue"] is None


def test_csv_preview_detects_semicolon_and_utf8_bom() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={
            "file": (
                "experiment.csv",
                "\ufeffgroup;value\nA;1\nB;2\n".encode(),
                "application/csv",
            )
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["delimiter"] == ";"
    assert payload["columns"][1]["inferred_type"] == "integer"


def test_csv_preview_accepts_explicit_tab_delimiter() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group\tvalue\nA\t1\n", "text/plain")},
        data={"delimiter": "\t"},
    )

    assert response.status_code == 200
    assert response.json()["delimiter"] == "\t"


def test_csv_preview_sanitizes_path_components_from_filename() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("../../unsafe.csv", b"group,value\nA,1\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "unsafe.csv"


def test_csv_preview_rejects_non_csv_extension() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.txt", b"group,value\nA,1\n", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_csv_preview_rejects_unsupported_content_type() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,value\nA,1\n", "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_csv_preview_rejects_non_utf8_content() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,value\nA,\xff\n", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_ENCODING"


def test_csv_preview_rejects_file_over_configured_limit(monkeypatch) -> None:
    monkeypatch.setenv("EXPERIMENTOS_MAX_CSV_BYTES", "10")

    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,value\nA,1\n", "text/csv")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert response.json()["error"]["details"]["max_bytes"] == 10


def test_csv_preview_rejects_invalid_delimiter() -> None:
    response = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,value\nA,1\n", "text/csv")},
        data={"delimiter": ":"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DELIMITER"


def test_csv_preview_rejects_duplicate_or_missing_columns() -> None:
    duplicate = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,group\nA,B\n", "text/csv")},
    )
    missing = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,\nA,1\n", "text/csv")},
    )

    assert duplicate.status_code == 400
    assert duplicate.json()["error"]["code"] == "DUPLICATE_COLUMNS"
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "MISSING_COLUMNS"


def test_csv_preview_rejects_empty_file_and_header_only_dataset() -> None:
    empty = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"", "text/csv")},
    )
    header_only = _client().post(
        "/api/v1/datasets/preview",
        files={"file": ("data.csv", b"group,value\n", "text/csv")},
    )

    assert empty.status_code == 400
    assert empty.json()["error"]["code"] == "EMPTY_FILE"
    assert header_only.status_code == 400
    assert header_only.json()["error"]["code"] == "EMPTY_DATASET"
