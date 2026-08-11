const API_PREFIX = "/api/v1";

async function postCsv(path, formData) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? "The CSV request failed.";
    throw new Error(message);
  }

  return response.json();
}

export function previewCsvDataset(file, delimiter = "") {
  const formData = new FormData();
  formData.append("file", file);
  if (delimiter) {
    formData.append("delimiter", delimiter);
  }
  return postCsv("/datasets/preview", formData);
}

export function validateCsvDataset(file, mapping) {
  const formData = new FormData();
  formData.append("file", file);
  Object.entries(mapping).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      formData.append(key, value);
    }
  });
  return postCsv("/datasets/validate", formData);
}
