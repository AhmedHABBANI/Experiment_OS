"""Public simulation interface."""

from experiment_os_stats.simulation.binary import (
    BinarySimulationResult,
    simulate_binary_ab,
)
from experiment_os_stats.simulation.continuous import (
    ContinuousDistribution,
    ContinuousSimulationResult,
    simulate_continuous_ab,
)

__all__ = [
    "BinarySimulationResult",
    "ContinuousDistribution",
    "ContinuousSimulationResult",
    "simulate_binary_ab",
    "simulate_continuous_ab",
]
