import { afterEach, describe, expect, it, vi } from "vitest";

import { analyzeContinuousExperiment } from "../api/analyses.js";

const dataset = {
  group_a: [1, 2, 3],
  group_b: [2, 3, 4]
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("continuous analysis API client", () => {
  it.each([
    ["student-t", "/api/v1/analyses/student-t"],
    ["welch-t", "/api/v1/analyses/welch-t"]
  ])("routes %s to its endpoint", async (test, expectedPath) => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ test_name: test })
    });

    await analyzeContinuousExperiment(dataset, {
      test,
      alpha: 0.05,
      alternative: "two-sided"
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expectedPath,
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining(`"alpha":0.05`)
      })
    );
  });
});
