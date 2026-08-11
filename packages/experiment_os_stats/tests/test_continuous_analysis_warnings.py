"""Tests for structured diagnostics returned by continuous analyses."""

import json
from collections.abc import Callable

import pytest

from experiment_os_stats import StatisticalResult, student_t_test, welch_t_test

type ContinuousTest = Callable[..., StatisticalResult]


@pytest.mark.parametrize("test", [student_t_test, welch_t_test])
def test_continuous_tests_warn_at_sample_size_imbalance_threshold(
    test: ContinuousTest,
) -> None:
    result = test([0.0, 1.0], [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])

    warning = next(item for item in result.warnings if item.code == "IMBALANCED_SAMPLE_SIZES")
    assert warning.details == {
        "n_a": 2,
        "n_b": 8,
        "size_ratio": 4.0,
        "warning_threshold": 4.0,
    }


@pytest.mark.parametrize("test", [student_t_test, welch_t_test])
def test_continuous_tests_report_iqr_outliers_by_group(test: ContinuousTest) -> None:
    result = test([0.0, 0.0, 0.0, 0.0, 10.0], [0.0, 0.0, 0.0, 1.0, 1.0])

    warning = next(item for item in result.warnings if item.code == "IQR_OUTLIERS_DETECTED")
    assert set(warning.details["groups"]) == {"group_a"}
    assert warning.details["groups"]["group_a"] == {
        "outlier_count": 1,
        "lower_fence": 0.0,
        "upper_fence": 0.0,
        "iqr": 0.0,
        "multiplier": 1.5,
    }


@pytest.mark.parametrize("test", [student_t_test, welch_t_test])
def test_continuous_tests_return_no_warnings_for_nominal_samples(
    test: ContinuousTest,
) -> None:
    result = test([-2.0, -1.0, 0.0, 1.0, 2.0], [-1.5, -0.5, 0.5, 1.5, 2.5])

    assert result.warnings == ()


def test_continuous_warning_payload_is_json_compatible() -> None:
    result = welch_t_test([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0], [1.0, 2.0])

    payload = result.to_dict()

    assert len(payload["warnings"]) == 2
    json.dumps(payload, allow_nan=False)
