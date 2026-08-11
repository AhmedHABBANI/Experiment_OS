import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../App.jsx";

vi.mock("react-plotly.js", () => ({
  default: ({ layout }) => <div data-testid="plotly-chart">{layout.title.text}</div>
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("App", () => {
  it("runs a binary simulation and renders the preview", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          metric_type: "binary",
          group_a: [0, 1],
          group_b: [1, null],
          metadata: {
            source: "simulation",
            seed: 42,
            n_a: 2,
            n_b: 2
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          metric_type: "binary",
          group_a: {
            n: 2,
            successes: 1,
            failures: 1,
            proportion: 0.5,
            standard_error: 0.353553
          },
          group_b: {
            n: 1,
            successes: 1,
            failures: 0,
            proportion: 1,
            standard_error: 0
          },
          comparison: {
            absolute_difference: 0.5,
            relative_uplift: 1,
            odds_ratio: null,
            risk_ratio: 2
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          groups: ["A", "B"],
          proportions: [0.5, 1],
          ci_lower: [0, 1],
          ci_upper: [1, 1],
          counts: [2, 1],
          successes: [1, 1]
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          test_name: "two_proportion_z_test",
          metric_type: "binary",
          statistic: 1.96,
          p_value: 0.049,
          alpha: 0.05,
          alternative: "two-sided",
          estimate: 0.5,
          confidence_interval: {
            lower: 0.01,
            upper: 0.99,
            level: 0.95,
            parameter: "difference_in_proportions_b_minus_a",
            method: "wald_unpooled"
          },
          effect_size: null,
          effect_size_name: null,
          reject_null: true,
          assumptions: [],
          warnings: [
            {
              code: "SMALL_EXPECTED_COUNT",
              message: "The normal approximation may be inaccurate.",
              severity: "warning",
              details: {}
            }
          ],
          interpretation: {
            null_hypothesis: "The population proportions are equal.",
            alternative_hypothesis: "The population proportions differ."
          },
          metadata: {}
        })
      });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Run simulation" }));

    await waitFor(() => expect(screen.getByText("Generated dataset")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Download CSV" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Group summaries" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Comparison" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Distribution diagnostics" })).toBeInTheDocument();
    expect(screen.getByText("Observed success rates")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Statistical analysis" })).toBeInTheDocument();
    expect(screen.getByText("Reject H0")).toBeInTheDocument();
    expect(screen.getByText("SMALL_EXPECTED_COUNT")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/simulations/binary",
      expect.objectContaining({ method: "POST" })
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/descriptive/binary",
      expect.objectContaining({ method: "POST" })
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/diagnostics/binary-rate",
      expect.objectContaining({ method: "POST" })
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/analyses/two-proportion-z",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("switches to the continuous form", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Continuous" }));

    expect(screen.getByRole("heading", { name: "Continuous simulation" })).toBeInTheDocument();
    expect(screen.getByLabelText("Distribution")).toBeInTheDocument();
  });

  it("allows the user to select Fisher exact manually", () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText("Test"), { target: { value: "fisher-exact" } });
    fireEvent.change(screen.getByLabelText("Alternative"), { target: { value: "greater" } });

    expect(screen.getByLabelText("Test")).toHaveValue("fisher-exact");
    expect(screen.getByLabelText("Alternative")).toHaveValue("greater");
  });
});
