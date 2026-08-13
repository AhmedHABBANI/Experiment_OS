"""Deterministic wording for resampling-based analyses."""

from typing import Literal

from experiment_os_stats.interpretation._common import (
    decision_message,
    practical_significance_message,
)
from experiment_os_stats.results import StatisticalInterpretation
from experiment_os_stats.types import Alternative


def _alternative_hypothesis(alternative: Alternative) -> str:
    if alternative is Alternative.TWO_SIDED:
        return "The population mean in group B differs from group A."
    direction = "greater" if alternative is Alternative.GREATER else "less"
    return f"The population mean in group B is {direction} than in group A."


type BootstrapEstimand = Literal["mean", "median"]


def _effect_message(estimate: float, *, estimand: str = "mean") -> str:
    if estimate > 0:
        return f"Group B's observed {estimand} is {estimate:.4g} units higher than group A's."
    if estimate < 0:
        return f"Group B's observed {estimand} is {abs(estimate):.4g} units lower than group A's."
    return f"The observed group {estimand}s are equal, a B-minus-A difference of 0 units."


def _bootstrap_interval_context(lower: float, upper: float) -> str:
    if lower > 0:
        return "The interval lies entirely above zero."
    if upper < 0:
        return "The interval lies entirely below zero."
    return (
        "The interval includes zero and remains compatible with either no difference "
        "or a difference."
    )


def interpret_permutation_mean_result(
    *,
    estimate: float,
    p_value: float,
    alpha: float,
    alternative: Alternative,
    n_permutations: int,
    seed: int | None,
) -> StatisticalInterpretation:
    """Build a cautious interpretation for a Monte-Carlo mean permutation test."""
    resolution = 1 / (n_permutations + 1)
    reproducibility = (
        f"Seed {seed} makes this Monte-Carlo permutation distribution reproducible."
        if seed is not None
        else "No seed was provided, so exact Monte-Carlo reproduction is not guaranteed."
    )
    return StatisticalInterpretation(
        question="Do the population means differ between independent groups A and B?",
        null_hypothesis=(
            "Group labels are exchangeable and the population mean difference is zero."
        ),
        alternative_hypothesis=_alternative_hypothesis(alternative),
        decision=decision_message(reject_null=p_value < alpha, alpha=alpha),
        effect=_effect_message(estimate),
        uncertainty=(
            f"The empirical p-value uses {n_permutations} random permutations with the "
            f"add-one correction, giving a minimum p-value resolution of {resolution:.4g}. "
            f"{reproducibility} This is Monte-Carlo uncertainty, not a confidence interval "
            "for the mean difference."
        ),
        practical_significance=practical_significance_message(),
    )


def interpret_bootstrap_difference_result(
    *,
    estimand: BootstrapEstimand,
    estimate: float,
    lower: float,
    upper: float,
    confidence_level: float,
    standard_error: float,
    n_resamples: int,
    seed: int | None,
) -> StatisticalInterpretation:
    """Build a cautious interpretation for a percentile bootstrap estimate."""
    reproducibility = (
        f"Seed {seed} makes the bootstrap distribution reproducible."
        if seed is not None
        else "No seed was provided, so exact bootstrap reproduction is not guaranteed."
    )
    percentage = confidence_level * 100
    return StatisticalInterpretation(
        question=(
            f"What is the population {estimand} difference between independent groups B and A?"
        ),
        null_hypothesis="Not applicable: this bootstrap procedure does not test a null hypothesis.",
        alternative_hypothesis=(
            "Not applicable: this bootstrap procedure estimates an effect rather than testing "
            "an alternative hypothesis."
        ),
        decision=(
            "No hypothesis-test decision is produced because this estimation procedure returns "
            "neither a p-value nor a null-hypothesis test."
        ),
        effect=_effect_message(estimate, estimand=estimand),
        uncertainty=(
            f"The {percentage:.3g}% percentile bootstrap interval is [{lower:.4g}, "
            f"{upper:.4g}], with bootstrap standard error {standard_error:.4g}, based on "
            f"{n_resamples} independent within-group resamples. "
            f"{_bootstrap_interval_context(lower, upper)} {reproducibility}"
        ),
        practical_significance=practical_significance_message(),
    )
