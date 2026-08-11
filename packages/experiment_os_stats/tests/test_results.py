"""Tests for the common statistical result models."""

import json
from math import nan

import pytest

from experiment_os_stats import (
    Alternative,
    ConfidenceInterval,
    MetricType,
    StatisticalResult,
    StatisticalWarning,
    WarningSeverity,
)


def test_confidence_interval_accepts_valid_boundaries() -> None:
    interval = ConfidenceInterval(
        lower=-1.5,
        upper=2.5,
        level=0.95,
        parameter="mean_difference",
        method="welch",
    )

    assert interval.lower == -1.5
    assert interval.upper == 2.5
    assert interval.level == 0.95
    assert interval.parameter == "mean_difference"
    assert interval.method == "welch"


def test_confidence_interval_rejects_invalid_level() -> None:
    with pytest.raises(
        ValueError,
        match="Confidence level must be strictly between 0 and 1",
    ):
        ConfidenceInterval(
            lower=0.0,
            upper=1.0,
            level=1.0,
        )


def test_confidence_interval_rejects_reversed_boundaries() -> None:
    with pytest.raises(
        ValueError,
        match=("The lower confidence bound cannot exceed the upper bound"),
    ):
        ConfidenceInterval(
            lower=2.0,
            upper=1.0,
        )


def test_confidence_interval_rejects_nan_boundaries() -> None:
    with pytest.raises(
        ValueError,
        match="Confidence interval boundaries cannot be NaN",
    ):
        ConfidenceInterval(
            lower=nan,
            upper=1.0,
        )


def test_confidence_interval_is_serializable() -> None:
    interval = ConfidenceInterval(
        lower=0.02,
        upper=0.08,
        level=0.95,
        parameter="difference_in_proportions",
        method="normal_approximation",
    )

    assert interval.to_dict() == {
        "lower": 0.02,
        "upper": 0.08,
        "level": 0.95,
        "parameter": "difference_in_proportions",
        "method": "normal_approximation",
    }


def test_statistical_warning_is_serializable() -> None:
    warning = StatisticalWarning(
        code="SMALL_EXPECTED_COUNT",
        message="The normal approximation may be inaccurate.",
        severity=WarningSeverity.WARNING,
        details={
            "minimum_expected_count": 3.8,
        },
    )

    assert warning.to_dict() == {
        "code": "SMALL_EXPECTED_COUNT",
        "message": "The normal approximation may be inaccurate.",
        "severity": "warning",
        "details": {
            "minimum_expected_count": 3.8,
        },
    }


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("", "Valid message"),
        ("   ", "Valid message"),
        ("VALID_CODE", ""),
        ("VALID_CODE", "   "),
    ],
)
def test_statistical_warning_rejects_empty_fields(
    code: str,
    message: str,
) -> None:
    with pytest.raises(ValueError):
        StatisticalWarning(
            code=code,
            message=message,
        )


def test_statistical_result_infers_rejection_decision() -> None:
    result = StatisticalResult(
        test_name="welch_t_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=2.41,
        p_value=0.017,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
    )

    assert result.reject_null is True


def test_statistical_result_does_not_reject_null() -> None:
    result = StatisticalResult(
        test_name="welch_t_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=0.71,
        p_value=0.48,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
    )

    assert result.reject_null is False


def test_p_value_equal_to_alpha_does_not_reject_null() -> None:
    result = StatisticalResult(
        test_name="example_test",
        metric_type=MetricType.CONTINUOUS,
        statistic=1.0,
        p_value=0.05,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
    )

    assert result.reject_null is False


@pytest.mark.parametrize(
    "invalid_p_value",
    [-0.01, 1.01, nan],
)
def test_statistical_result_rejects_invalid_p_value(
    invalid_p_value: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=("p_value must be a finite value between 0 and 1"),
    ):
        StatisticalResult(
            test_name="invalid_test",
            metric_type=MetricType.CONTINUOUS,
            statistic=0.0,
            p_value=invalid_p_value,
            alpha=0.05,
            alternative=Alternative.TWO_SIDED,
        )


@pytest.mark.parametrize(
    "invalid_alpha",
    [0.0, 1.0, -0.1, 1.1],
)
def test_statistical_result_rejects_invalid_alpha(
    invalid_alpha: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="alpha must be strictly between 0 and 1",
    ):
        StatisticalResult(
            test_name="example_test",
            metric_type=MetricType.CONTINUOUS,
            alpha=invalid_alpha,
            alternative=Alternative.TWO_SIDED,
        )


def test_statistical_result_rejects_empty_test_name() -> None:
    with pytest.raises(
        ValueError,
        match="test_name cannot be empty",
    ):
        StatisticalResult(
            test_name="   ",
            metric_type=MetricType.CONTINUOUS,
            alpha=0.05,
            alternative=Alternative.TWO_SIDED,
        )


def test_explicit_decision_must_match_p_value() -> None:
    with pytest.raises(
        ValueError,
        match=("reject_null is inconsistent with p_value and alpha"),
    ):
        StatisticalResult(
            test_name="example_test",
            metric_type=MetricType.CONTINUOUS,
            statistic=2.0,
            p_value=0.01,
            alpha=0.05,
            alternative=Alternative.TWO_SIDED,
            reject_null=False,
        )


def test_effect_size_requires_a_name() -> None:
    with pytest.raises(
        ValueError,
        match=("effect_size_name is required when effect_size is provided"),
    ):
        StatisticalResult(
            test_name="example_test",
            metric_type=MetricType.CONTINUOUS,
            alpha=0.05,
            alternative=Alternative.TWO_SIDED,
            effect_size=0.4,
        )


def test_effect_size_name_requires_a_value() -> None:
    with pytest.raises(
        ValueError,
        match=("effect_size must be provided when effect_size_name is set"),
    ):
        StatisticalResult(
            test_name="example_test",
            metric_type=MetricType.CONTINUOUS,
            alpha=0.05,
            alternative=Alternative.TWO_SIDED,
            effect_size_name="cohens_d",
        )


def test_statistical_result_rejects_empty_assumption() -> None:
    with pytest.raises(
        ValueError,
        match="Assumptions cannot contain empty strings",
    ):
        StatisticalResult(
            test_name="example_test",
            metric_type=MetricType.CONTINUOUS,
            alpha=0.05,
            alternative=Alternative.TWO_SIDED,
            assumptions=(
                "The observations are independent.",
                "",
            ),
        )


def test_statistical_result_is_json_compatible() -> None:
    result = StatisticalResult(
        test_name="two_proportion_z_test",
        metric_type=MetricType.BINARY,
        statistic=2.1,
        p_value=0.036,
        alpha=0.05,
        alternative=Alternative.TWO_SIDED,
        estimate=0.04,
        confidence_interval=ConfidenceInterval(
            lower=0.002,
            upper=0.078,
            parameter="difference_in_proportions",
            method="normal_approximation",
        ),
        effect_size=1.25,
        effect_size_name="odds_ratio",
        assumptions=(
            "The observations are independent.",
            "The normal approximation is sufficiently accurate.",
        ),
        warnings=(
            StatisticalWarning(
                code="SMALL_EXPECTED_COUNT",
                message=("One expected count is close to the recommended limit."),
                severity=WarningSeverity.WARNING,
            ),
        ),
        interpretation={
            "decision": ("The null hypothesis is rejected at the selected alpha level."),
        },
        metadata={
            "n_a": 1000,
            "n_b": 1000,
        },
    )

    payload = result.to_dict()
    serialized = json.dumps(payload)

    assert isinstance(serialized, str)
    assert payload["metric_type"] == "binary"
    assert payload["alternative"] == "two-sided"
    assert payload["reject_null"] is True
    assert payload["confidence_interval"]["level"] == 0.95
    assert payload["effect_size_name"] == "odds_ratio"
    assert payload["warnings"][0]["code"] == "SMALL_EXPECTED_COUNT"
    assert payload["metadata"]["n_a"] == 1000
