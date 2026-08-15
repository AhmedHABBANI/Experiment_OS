const API_PREFIX = "/api/v1";

export async function exportJsonReport(payload) {
  return exportReport("json", payload, "The JSON export request failed.");
}

export async function exportResultsCsv(payload) {
  return exportReport("csv", payload, "The results CSV export request failed.");
}

export async function exportAnalyzedDataCsv(dataset) {
  return exportReport("csv/data", { dataset }, "The analyzed-data CSV export request failed.");
}

async function exportReport(format, payload, fallbackMessage) {
  const response = await fetch(`${API_PREFIX}/exports/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? fallbackMessage;
    throw new Error(message);
  }

  return response.text();
}
