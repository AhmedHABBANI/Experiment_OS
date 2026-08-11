"""Simulation endpoints."""

from fastapi import APIRouter

from app.schemas.simulations import (
    BinarySimulationRequest,
    ContinuousSimulationRequest,
    SimulationResponse,
)
from app.services.simulation_service import run_binary_simulation, run_continuous_simulation

router = APIRouter()


@router.post("/binary", response_model=SimulationResponse)
def simulate_binary(request: BinarySimulationRequest) -> SimulationResponse:
    """Simulate a binary A/B experiment."""
    return run_binary_simulation(request)


@router.post("/continuous", response_model=SimulationResponse)
def simulate_continuous(request: ContinuousSimulationRequest) -> SimulationResponse:
    """Simulate a continuous A/B experiment."""
    return run_continuous_simulation(request)
