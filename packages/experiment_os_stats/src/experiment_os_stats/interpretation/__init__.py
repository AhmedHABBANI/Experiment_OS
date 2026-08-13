"""Public deterministic-interpretation interface."""

from experiment_os_stats.interpretation.binary import interpret_binary_result
from experiment_os_stats.interpretation.continuous import interpret_continuous_parametric_result
from experiment_os_stats.interpretation.nonparametric import interpret_mann_whitney_result

__all__ = [
    "interpret_binary_result",
    "interpret_continuous_parametric_result",
    "interpret_mann_whitney_result",
]
