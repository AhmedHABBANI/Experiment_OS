"""Tests for manual CSV mapping to normalized A/B datasets."""

from fastapi.testclient import TestClient

from app.main import create_app


def _post_mapping(content: bytes, **mapping):
    defaults = {
        "group_column": "group",
        "group_a_value": "A",
        "group_b_value": "B",
        "metric_column": "metric",
        "metric_type": "continuous",
    }
    defaults.update(mapping)
    return TestClient(create_app()).post(
        "/api/v1/datasets/validate",
        files={"file": ("experiment.csv", content, "text/csv")},
        data=defaults,
    )


def test_csv_mapping_normalizes_continuous_groups_and_summarizes_exclusions() -> None:
    response = _post_mapping(b"group,metric\nA,1.5\nB,2.5\nC,3\nA,bad\nB,\nA,4\n")

    payload = response.json()

    assert response.status_code == 200
    assert payload["metric_type"] == "continuous"
    assert payload["group_a"] == [1.5, 4.0]
    assert payload["group_b"] == [2.5]
    assert payload["metadata"]["original_rows"] == 6
    assert payload["metadata"]["retained_rows"] == 3
    assert payload["metadata"]["excluded_rows"] == 3
    assert payload["metadata"]["exclusion_reasons"] == {
        "missing_group": 0,
        "unmapped_group": 1,
        "missing_metric": 1,
        "invalid_metric": 1,
    }
    assert payload["metadata"]["source"] == "csv_import"


def test_csv_mapping_maps_binary_modalities_to_zero_and_one() -> None:
    response = _post_mapping(
        b"group,metric\nA,yes\nA,no\nB,YES\nB,no\nB,maybe\nC,yes\n",
        metric_type="binary",
        binary_success_value="yes",
        binary_failure_value="no",
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["metric_type"] == "binary"
    assert payload["group_a"] == [1.0, 0.0]
    assert payload["group_b"] == [1.0, 0.0]
    assert payload["metadata"]["exclusion_reasons"]["invalid_metric"] == 1
    assert payload["metadata"]["exclusion_reasons"]["unmapped_group"] == 1


def test_csv_mapping_supports_numeric_binary_values_and_selected_delimiter() -> None:
    response = _post_mapping(
        b"arm;outcome\n0;1\n0;0\n1;1\n1;0\n",
        delimiter=";",
        group_column="arm",
        group_a_value="0",
        group_b_value="1",
        metric_column="outcome",
        metric_type="binary",
        binary_success_value="1",
        binary_failure_value="0",
    )

    assert response.status_code == 200
    assert response.json()["group_a"] == [1.0, 0.0]
    assert response.json()["group_b"] == [1.0, 0.0]
    assert response.json()["metadata"]["delimiter"] == ";"


def test_csv_mapping_rejects_missing_mapped_columns() -> None:
    response = _post_mapping(
        b"group,value\nA,1\nB,2\n",
        metric_column="metric",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_COLUMNS"
    assert response.json()["error"]["details"]["missing_columns"] == ["metric"]


def test_csv_mapping_rejects_same_group_and_metric_column() -> None:
    response = _post_mapping(
        b"group,metric\nA,1\nB,2\n",
        metric_column="group",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MAPPING"


def test_csv_mapping_rejects_identical_group_values() -> None:
    response = _post_mapping(
        b"group,metric\nA,1\nB,2\n",
        group_b_value="A",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_GROUP_MAPPING"


def test_csv_mapping_requires_complete_binary_mapping() -> None:
    response = _post_mapping(
        b"group,metric\nA,yes\nB,no\n",
        metric_type="binary",
        binary_success_value="yes",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_BINARY_MAPPING"


def test_csv_mapping_rejects_unsupported_metric_type() -> None:
    response = _post_mapping(
        b"group,metric\nA,1\nB,2\n",
        metric_type="count",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_METRIC_TYPE"


def test_csv_mapping_rejects_when_one_group_has_no_valid_rows() -> None:
    response = _post_mapping(
        b"group,metric\nA,1\nB,bad\nC,2\n",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INSUFFICIENT_GROUP_DATA"
    assert response.json()["error"]["details"]["retained_b"] == 0


def test_csv_mapping_counts_missing_groups_separately() -> None:
    response = _post_mapping(
        b"group,metric\nA,1\n,3\nB,2\n",
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["exclusion_reasons"]["missing_group"] == 1
