"""Tests for the shared ExperimentOS enumerations."""

import json

from experiment_os_stats import (
    Alternative,
    DataSource,
    MetricType,
    WarningSeverity,
)


def test_metric_type_values_are_stable() -> None:
    assert MetricType.BINARY.value == "binary"
    assert MetricType.CONTINUOUS.value == "continuous"


def test_alternative_values_are_stable() -> None:
    assert Alternative.TWO_SIDED.value == "two-sided"
    assert Alternative.GREATER.value == "greater"
    assert Alternative.LESS.value == "less"


def test_data_source_values_are_stable() -> None:
    assert DataSource.SIMULATION.value == "simulation"
    assert DataSource.CSV_IMPORT.value == "csv_import"


def test_warning_severity_values_are_stable() -> None:
    assert WarningSeverity.INFO.value == "info"
    assert WarningSeverity.WARNING.value == "warning"
    assert WarningSeverity.ERROR.value == "error"


def test_string_enums_are_json_serializable() -> None:
    payload = {
        "metric_type": MetricType.BINARY,
        "alternative": Alternative.TWO_SIDED,
    }

    serialized = json.dumps(payload)

    assert serialized == ('{"metric_type": "binary", "alternative": "two-sided"}')
