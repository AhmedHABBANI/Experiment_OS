import { afterEach, describe, expect, it, vi } from "vitest";

import { exportJsonReport } from "../api/exports.js";

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
});
