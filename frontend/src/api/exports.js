const API_PREFIX = "/api/v1";

export async function exportJsonReport(payload) {
  const response = await fetch(`${API_PREFIX}/exports/json`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? "The JSON export request failed.";
    throw new Error(message);
  }

  return response.text();
}
