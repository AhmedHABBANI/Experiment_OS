"""Shared deterministic-interpretation wording."""

from experiment_os_stats.results import StatisticalWarning


def decision_message(*, reject_null: bool, alpha: float) -> str:
    """Describe a frequentist decision without accepting the null hypothesis."""
    threshold = f"{alpha:.3g}"
    if reject_null:
        return (
            "The data provide sufficient evidence to reject the null hypothesis "
            f"at alpha = {threshold}."
        )
    return (
        "The data do not provide sufficient evidence to reject the null hypothesis "
        f"at alpha = {threshold}; this does not establish that the null hypothesis is true."
    )


def practical_significance_message() -> str:
    """State why practical importance is deliberately left unresolved."""
    return (
        "Practical significance was not assessed because no practical-effect "
        "threshold was provided."
    )


def warning_context(warnings: tuple[StatisticalWarning, ...]) -> str | None:
    """Contextualize structured warnings without changing their content."""
    if not warnings:
        return None
    return "Review the analysis warnings before relying on this conclusion: " + "; ".join(
        warning.message for warning in warnings
    )
