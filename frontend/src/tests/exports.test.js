import { afterEach, describe, expect, it, vi } from "vitest";

import {
  exportAnalyzedDataCsv,
  exportJsonReport,
  exportPdfReport,
  exportResultsCsv
} from "../api/exports.js";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("JSON export API client", () => {
  it("posts the complete report state and returns the server artifact unchanged", async () => {
    const report = {
      source: "simulation",
      configuration: { analysis: { test: "welch-t" } },
      dataset: { metric_type: "continuous", group_a: [1, 2], group_b: [2, 3], metadata: {} },
      descriptive_summary: { metric_type: "continuous", group_a: {}, group_b: {}, comparison: {} },
      analysis_result: { test_name: "welch_t_test", p_value: 0.031 }
    };
    const serverArtifact = '{"schema_version":"1.0","analysis_result":{"p_value":0.031}}';
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      text: async () => serverArtifact
    });

    const content = await exportJsonReport(report);

    expect(content).toBe(serverArtifact);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/exports/json",
      expect.objectContaining({ method: "POST", body: JSON.stringify(report) })
    );
  });

  it("surfaces a controlled export error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: async () => ({ error: { message: "The report is incomplete." } })
    });

    await expect(exportJsonReport({})).rejects.toThrow("The report is incomplete.");
  });

  it("returns the flattened results CSV artifact unchanged", async () => {
    const csv = "field,value\nanalysis_result.p_value,0.031\n";
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, text: async () => csv });

    const content = await exportResultsCsv({ source: "simulation" });

    expect(content).toBe(csv);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/exports/csv",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("posts a normalized dataset and returns the analyzed-data CSV unchanged", async () => {
    const dataset = { metric_type: "binary", group_a: [0, 1], group_b: [1], metadata: {} };
    const csv = "group,observation,value\nA,1,0.0\nA,2,1.0\nB,1,1.0\n";
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, text: async () => csv });

    const content = await exportAnalyzedDataCsv(dataset);

    expect(content).toBe(csv);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/exports/csv/data",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ dataset }) })
    );
  });

  it("returns the PDF report blob unchanged", async () => {
    const report = { source: "simulation", dataset: { metric_type: "continuous" } };
    const pdf = new Blob(["%PDF-test"], { type: "application/pdf" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: true, blob: async () => pdf });

    const content = await exportPdfReport(report);

    expect(content).toBe(pdf);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/reports/pdf",
      expect.objectContaining({ method: "POST", body: JSON.stringify(report) })
    );
  });
});
