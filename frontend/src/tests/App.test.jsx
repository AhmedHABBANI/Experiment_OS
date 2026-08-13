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
    expect(screen.getByLabelText("Test")).toHaveValue("student-t");
    expect(screen.getByLabelText("Test")).toBeDisabled();
  });

  it("runs a continuous simulation with the Student t-test", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          metric_type: "continuous",
          group_a: [9, 10, 11],
          group_b: [12, 13, 14],
          metadata: { source: "simulation", seed: 42, n_a: 3, n_b: 3 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          metric_type: "continuous",
          group_a: { n: 3, mean: 10, median: 10, standard_deviation: 1, standard_error: 0.577, iqr: 1 },
          group_b: { n: 3, mean: 13, median: 13, standard_deviation: 1, standard_error: 0.577, iqr: 1 },
          comparison: { mean_difference: 3, median_difference: 3, mean_ratio: 1.3 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          histograms: { A: { bin_edges: [9, 11], counts: [3] }, B: { bin_edges: [12, 14], counts: [3] } },
          boxplots: {
            A: { minimum: 9, q1: 9.5, median: 10, q3: 10.5, maximum: 11 },
            B: { minimum: 12, q1: 12.5, median: 13, q3: 13.5, maximum: 14 }
          },
          qq_plots: {
            A: { theoretical_quantiles: [-1, 0, 1], sample_quantiles: [9, 10, 11] },
            B: { theoretical_quantiles: [-1, 0, 1], sample_quantiles: [12, 13, 14] }
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          test_name: "student_t_test",
          metric_type: "continuous",
          statistic: 3.674,
          p_value: 0.021,
          alpha: 0.05,
          alternative: "greater",
          estimate: 3,
          confidence_interval: {
            lower: 0.733,
            upper: 5.267,
            level: 0.95,
            parameter: "difference_in_means_b_minus_a",
            method: "student_t_pooled"
          },
          effect_size: 3,
          effect_size_name: "cohens_d",
          reject_null: true,
          assumptions: [],
          warnings: [],
          interpretation: {
            question: "Do the population means differ between groups A and B?",
            null_hypothesis: "The population means are equal.",
            alternative_hypothesis: "The population mean in B is greater than A.",
            decision: "The data provide sufficient evidence to reject the null hypothesis.",
            effect: "Group B's observed mean is 3 units higher than group A's.",
            uncertainty: "The confidence interval lies entirely above zero.",
            practical_significance: "Practical significance was not assessed."
          },
          metadata: { difference_direction: "group_b_minus_group_a" }
        })
      });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Continuous" }));
    fireEvent.change(screen.getByLabelText("Alternative"), { target: { value: "greater" } });
    fireEvent.click(screen.getByRole("button", { name: "Run simulation" }));

    await screen.findByRole("heading", { name: "Statistical analysis" });
    expect(screen.getByText("Student T Test")).toBeInTheDocument();
    expect(screen.getByText("Reject H0")).toBeInTheDocument();
    expect(screen.getByLabelText("Deterministic interpretation")).toHaveTextContent(
      "Group B's observed mean is 3 units higher"
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/analyses/student-t",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"alternative":"greater"')
      })
    );
  });

  it("allows the user to select Fisher exact manually", () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText("Test"), { target: { value: "fisher-exact" } });
    fireEvent.change(screen.getByLabelText("Alternative"), { target: { value: "greater" } });

    expect(screen.getByLabelText("Test")).toHaveValue("fisher-exact");
    expect(screen.getByLabelText("Alternative")).toHaveValue("greater");
  });

  it("previews, maps and analyzes an imported continuous CSV", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          filename: "experiment.csv",
          size_bytes: 42,
          delimiter: ",",
          row_count: 4,
          columns: [
            { name: "variant", inferred_type: "string", missing_count: 0 },
            { name: "revenue", inferred_type: "number", missing_count: 1 }
          ],
          preview_rows: [
            { variant: "control", revenue: 10 },
            { variant: "treatment", revenue: 12 }
          ]
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          metric_type: "continuous",
          group_a: [10],
          group_b: [12, 13],
          metadata: {
            source: "csv_import",
            filename: "experiment.csv",
            original_rows: 4,
            retained_rows: 3,
            excluded_rows: 1,
            exclusion_reasons: { missing_metric: 1 },
            validation: {
              group_a: { valid_size: 1 },
              group_b: { valid_size: 2 }
            }
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          metric_type: "continuous",
          group_a: { n: 1, mean: 10, median: 10, standard_deviation: 0, standard_error: 0, iqr: 0 },
          group_b: { n: 2, mean: 12.5, median: 12.5, standard_deviation: 0.707, standard_error: 0.5, iqr: 0.5 },
          comparison: { mean_difference: 2.5, median_difference: 2.5, mean_ratio: 1.25 }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          histograms: {
            A: { bin_edges: [9, 11], counts: [1] },
            B: { bin_edges: [12, 14], counts: [2] }
          },
          boxplots: {
            A: { minimum: 10, q1: 10, median: 10, q3: 10, maximum: 10 },
            B: { minimum: 12, q1: 12.25, median: 12.5, q3: 12.75, maximum: 13 }
          },
          qq_plots: {
            A: { theoretical_quantiles: [0], sample_quantiles: [10] },
            B: { theoretical_quantiles: [-0.5, 0.5], sample_quantiles: [12, 13] }
          }
        })
      });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Import CSV" }));
    const file = new File(["variant,revenue\ncontrol,10\ntreatment,12"], "experiment.csv", { type: "text/csv" });
    fireEvent.change(screen.getByLabelText("CSV file"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Preview CSV" }));

    await screen.findByRole("heading", { name: "experiment.csv" });
    expect(screen.getByText((_, element) => element?.textContent === "revenue number, 1 missing")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Group A value"), { target: { value: "control" } });
    fireEvent.change(screen.getByLabelText("Group B value"), { target: { value: "treatment" } });
    fireEvent.click(screen.getByRole("button", { name: "Validate dataset" }));

    await screen.findByRole("heading", { name: "Imported dataset" });
    expect(screen.getByRole("heading", { name: "Import validation" })).toBeInTheDocument();
    expect(screen.getByText("Group B retained").nextElementSibling).toHaveTextContent("2");
    expect(screen.getByText("missing metric: 1")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      1,
      "/api/v1/datasets/preview",
      expect.objectContaining({ method: "POST", body: expect.any(FormData) })
    );
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      2,
      "/api/v1/datasets/validate",
      expect.objectContaining({ method: "POST", body: expect.any(FormData) })
    );
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/v1/descriptive/continuous",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("shows explicit success and failure mapping for binary CSV metrics", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        filename: "conversion.csv",
        size_bytes: 30,
        delimiter: ";",
        row_count: 2,
        columns: [
          { name: "arm", inferred_type: "string", missing_count: 0 },
          { name: "converted", inferred_type: "string", missing_count: 0 }
        ],
        preview_rows: [{ arm: "A", converted: "yes" }]
      })
    });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Import CSV" }));
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: { files: [new File(["arm;converted\nA;yes"], "conversion.csv", { type: "text/csv" })] }
    });
    fireEvent.change(screen.getByLabelText("Delimiter"), { target: { value: ";" } });
    fireEvent.click(screen.getByRole("button", { name: "Preview CSV" }));

    await screen.findByRole("heading", { name: "conversion.csv" });
    fireEvent.change(screen.getByLabelText("Metric type"), { target: { value: "binary" } });

    expect(screen.getByLabelText("Success value (1)")).toBeRequired();
    expect(screen.getByLabelText("Failure value (0)")).toBeRequired();
  });
});
