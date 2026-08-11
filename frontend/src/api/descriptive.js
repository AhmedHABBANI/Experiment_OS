const API_PREFIX = "/api/v1";

async function postDescriptive(path, payload) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? "The descriptive summary request failed.";
    throw new Error(message);
  }

  return response.json();
}

export function summarizeBinaryExperiment(payload) {
  return postDescriptive("/descriptive/binary", {
    group_a: payload.group_a,
    group_b: payload.group_b
  });
}

export function summarizeContinuousExperiment(payload) {
  return postDescriptive("/descriptive/continuous", {
    group_a: payload.group_a,
    group_b: payload.group_b
  });
}
