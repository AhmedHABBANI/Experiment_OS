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
    ["welch-t", "/api/v1/analyses/welch-t"],
    ["mann-whitney", "/api/v1/analyses/mann-whitney"],
    ["permutation", "/api/v1/analyses/permutation"],
    ["bootstrap", "/api/v1/analyses/bootstrap-difference"]
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
        body: expect.stringContaining('"group_a":[1,2,3]')
      })
    );
  });

  it("sends permutation count and seed only for permutation", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ test_name: "permutation_mean_test" })
    });

    await analyzeContinuousExperiment(dataset, {
      test: "permutation",
      alpha: 0.05,
      alternative: "greater",
      n_permutations: 500,
      seed: 42
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/analyses/permutation",
      expect.objectContaining({
        body: expect.stringContaining('"n_permutations":500,"seed":42')
      })
    );
  });

  it("sends bootstrap estimand, confidence and reproducibility options", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ test_name: "bootstrap_median_difference" })
    });

    await analyzeContinuousExperiment(dataset, {
      test: "bootstrap",
      alpha: 0.05,
      alternative: "two-sided",
      estimand: "median",
      confidence_level: 0.9,
      n_resamples: 500,
      seed: 42
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/analyses/bootstrap-difference",
      expect.objectContaining({
        body: expect.stringContaining(
          '"estimand":"median","confidence_level":0.9,"n_resamples":500,"seed":42'
        )
      })
    );
    const requestBody = JSON.parse(globalThis.fetch.mock.calls[0][1].body);
    expect(requestBody).not.toHaveProperty("alpha");
    expect(requestBody).not.toHaveProperty("alternative");
  });
});
