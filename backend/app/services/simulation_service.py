"""Simulation service functions."""

from app.schemas.simulations import (
    BinarySimulationRequest,
    ContinuousSimulationRequest,
    SimulationResponse,
)
from experiment_os_stats import simulate_binary_ab, simulate_continuous_ab


def run_binary_simulation(request: BinarySimulationRequest) -> SimulationResponse:
    """Run a binary simulation using the statistics package."""
    result = simulate_binary_ab(**request.model_dump())
    return SimulationResponse(**result.to_dict())


def run_continuous_simulation(request: ContinuousSimulationRequest) -> SimulationResponse:
    """Run a continuous simulation using the statistics package."""
    result = simulate_continuous_ab(**request.model_dump())
    return SimulationResponse(**result.to_dict())
