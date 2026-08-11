const API_PREFIX = "/api/v1";

async function postSimulation(path, payload) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? "The simulation request failed.";
    throw new Error(message);
  }

  return response.json();
}

export function simulateBinaryExperiment(payload) {
  return postSimulation("/simulations/binary", payload);
}

export function simulateContinuousExperiment(payload) {
  return postSimulation("/simulations/continuous", payload);
}
