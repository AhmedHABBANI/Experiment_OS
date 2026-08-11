const API_PREFIX = "/api/v1";

async function postDiagnostics(path, payload) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? "The diagnostic data request failed.";
    throw new Error(message);
  }

  return response.json();
}

export function fetchBinaryDiagnostics(payload) {
  return postDiagnostics("/diagnostics/binary-rate", {
    group_a: payload.group_a,
    group_b: payload.group_b
  });
}

export function fetchContinuousDiagnostics(payload, bins = 12) {
  return postDiagnostics("/diagnostics/continuous-distribution", {
    group_a: payload.group_a,
    group_b: payload.group_b,
    bins
  });
}
