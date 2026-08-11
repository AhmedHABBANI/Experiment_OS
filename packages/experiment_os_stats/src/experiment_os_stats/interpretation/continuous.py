"""Deterministic wording for independent parametric continuous analyses."""

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


def _alternative_hypothesis(alternative: Alternative) -> str:
    if alternative is Alternative.TWO_SIDED:
        return "The population mean in group B differs from group A."
    direction = "greater" if alternative is Alternative.GREATER else "less"
    return f"The population mean in group B is {direction} than in group A."


def _effect_message(estimate: float, cohens_d: float) -> str:
    if estimate > 0:
        comparison = f"{abs(estimate):.4g} units higher"
    elif estimate < 0:
        comparison = f"{abs(estimate):.4g} units lower"
    else:
        comparison = "equal"
    return (
        f"Group B's observed mean is {comparison} than group A's observed mean; "
        f"the standardized difference is Cohen's d = {cohens_d:.3f}."
        if estimate != 0
        else "The observed group means are equal; the standardized difference is Cohen's d = 0.000."
    )


def _uncertainty_message(confidence_interval: ConfidenceInterval) -> str:
    if confidence_interval.lower <= 0 <= confidence_interval.upper:
        compatibility = "includes zero and remains compatible with effects in either direction"
    elif confidence_interval.lower > 0:
        compatibility = "lies above zero and is compatible only with a higher mean in group B"
    else:
        compatibility = "lies below zero and is compatible only with a lower mean in group B"
    return (
        f"The {confidence_interval.level * 100:.0f}% confidence interval for B minus A is "
        f"[{confidence_interval.lower:.4g}, {confidence_interval.upper:.4g}] units; "
        f"it {compatibility}."
    )


def interpret_continuous_parametric_result(
    *,
    estimate: float,
    cohens_d: float,
    p_value: float,
    alpha: float,
    alternative: Alternative,
    confidence_interval: ConfidenceInterval,
    warnings: tuple[StatisticalWarning, ...] = (),
) -> StatisticalInterpretation:
    """Build a cautious interpretation for an independent Student or Welch test."""
    return StatisticalInterpretation(
        question="Do the population means differ between independent groups A and B?",
        null_hypothesis="The population means in groups A and B are equal.",
        alternative_hypothesis=_alternative_hypothesis(alternative),
        decision=decision_message(reject_null=p_value < alpha, alpha=alpha),
        effect=_effect_message(estimate, cohens_d),
        uncertainty=_uncertainty_message(confidence_interval),
        practical_significance=practical_significance_message(),
        warning_context=warning_context(warnings),
    )
