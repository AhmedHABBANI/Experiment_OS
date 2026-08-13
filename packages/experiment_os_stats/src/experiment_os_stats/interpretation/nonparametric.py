"""Deterministic wording for independent rank-based analyses."""

from experiment_os_stats.interpretation._common import (
    decision_message,
    practical_significance_message,
    warning_context,
)
from experiment_os_stats.results import StatisticalInterpretation, StatisticalWarning


def _effect_message(rank_biserial: float, probability_of_superiority: float) -> str:
    if rank_biserial > 0:
        direction = "higher ranks in group B"
    elif rank_biserial < 0:
        direction = "higher ranks in group A"
    else:
        direction = "no observed rank tendency toward either group"
    return (
        f"The rank-biserial correlation is {rank_biserial:.3f}, indicating {direction}. "
        "The estimated probability that a randomly selected B observation exceeds an A "
        f"observation, with ties counting one half, is {probability_of_superiority:.3f}."
    )


def interpret_mann_whitney_result(
    *,
    rank_biserial: float,
    probability_of_superiority: float,
    p_value: float,
    alpha: float,
    warnings: tuple[StatisticalWarning, ...],
) -> StatisticalInterpretation:
    """Build a cautious interpretation for a two-sided Mann-Whitney U result."""
    return StatisticalInterpretation(
        question="Do the rank distributions differ between independent groups A and B?",
        null_hypothesis=(
            "A randomly selected observation from group B is equally likely to rank "
            "above or below one from group A."
        ),
        alternative_hypothesis="The distributions of ranks differ between groups A and B.",
        decision=decision_message(reject_null=p_value < alpha, alpha=alpha),
        effect=_effect_message(rank_biserial, probability_of_superiority),
        uncertainty=(
            "This result does not include a confidence interval for the rank effect, "
            "so its estimation uncertainty is not quantified here."
        ),
        practical_significance=practical_significance_message(),
        warning_context=warning_context(warnings),
    )
