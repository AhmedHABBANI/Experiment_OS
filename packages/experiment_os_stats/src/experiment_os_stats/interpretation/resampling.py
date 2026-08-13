"""Deterministic wording for resampling-based analyses."""

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


def _effect_message(estimate: float) -> str:
    if estimate > 0:
        return f"Group B's observed mean is {estimate:.4g} units higher than group A's."
    if estimate < 0:
        return f"Group B's observed mean is {abs(estimate):.4g} units lower than group A's."
    return "The observed group means are equal, a B-minus-A difference of 0 units."


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
