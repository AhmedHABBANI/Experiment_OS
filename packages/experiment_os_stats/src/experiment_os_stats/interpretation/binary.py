"""Deterministic wording for independent binary A/B analyses."""

from experiment_os_stats.interpretation._common import (
    decision_message,
    practical_significance_message,
    warning_context,
)
from experiment_os_stats.results import (
    ConfidenceInterval,
    StatisticalInterpretation,
    StatisticalWarning,
)
from experiment_os_stats.types import Alternative


def _alternative_hypothesis(alternative: Alternative, *, fisher: bool) -> str:
    if alternative is Alternative.TWO_SIDED:
        return (
            "The outcome and group membership are associated."
            if fisher
            else "The population proportion in group B differs from group A."
        )
    direction = "greater" if alternative is Alternative.GREATER else "less"
    quantity = "odds of success" if fisher else "population proportion"
    return f"The {quantity} in group B is {direction} than in group A."


def _effect_message(estimate: float) -> str:
    points = abs(estimate) * 100
    if estimate > 0:
        direction = "higher"
    elif estimate < 0:
        direction = "lower"
    else:
        return "The observed success rates are equal, a difference of 0 percentage points."
    return (
        f"Group B's observed success rate is {points:.2f} percentage points "
        f"{direction} than group A's."
    )


def _uncertainty_message(confidence_interval: ConfidenceInterval | None) -> str:
    if confidence_interval is None:
        return (
            "This result does not include a confidence interval for the rate difference, "
            "so its estimation uncertainty is not quantified here."
        )
    lower = confidence_interval.lower * 100
    upper = confidence_interval.upper * 100
    level = confidence_interval.level * 100
    if confidence_interval.lower <= 0 <= confidence_interval.upper:
        compatibility = "includes zero and remains compatible with effects in either direction"
    elif confidence_interval.lower > 0:
        compatibility = "lies above zero and is compatible only with a higher rate in group B"
    else:
        compatibility = "lies below zero and is compatible only with a lower rate in group B"
    return (
        f"The {level:.0f}% confidence interval for B minus A is "
        f"[{lower:.2f}, {upper:.2f}] percentage points; it {compatibility}."
    )


def interpret_binary_result(
    *,
    test_name: str,
    estimate: float,
    p_value: float,
    alpha: float,
    alternative: Alternative,
    confidence_interval: ConfidenceInterval | None,
    warnings: tuple[StatisticalWarning, ...] = (),
) -> StatisticalInterpretation:
    """Build a stable, cautious interpretation for a binary A/B test result."""
    fisher = test_name == "fisher_exact_test"
    return StatisticalInterpretation(
        question="Do the binary success rates differ between independent groups A and B?",
        null_hypothesis=(
            "The outcome and group membership are independent."
            if fisher
            else "The population proportions in groups A and B are equal."
        ),
        alternative_hypothesis=_alternative_hypothesis(alternative, fisher=fisher),
        decision=decision_message(reject_null=p_value < alpha, alpha=alpha),
        effect=_effect_message(estimate),
        uncertainty=_uncertainty_message(confidence_interval),
        practical_significance=practical_significance_message(),
        warning_context=warning_context(warnings),
    )
