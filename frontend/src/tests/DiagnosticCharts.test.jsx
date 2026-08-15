import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import DiagnosticCharts from "../components/DiagnosticCharts.jsx";

vi.mock("react-plotly.js", () => ({
  default: ({ config, data, layout }) => (
    <div
      data-testid="plotly-chart"
      data-grid-color={layout.yaxis.gridcolor}
      data-marker-color={data[0].marker.color}
      data-responsive={config.responsive}
    >
      {layout.title.text}
    </div>
  )
}));

afterEach(cleanup);

it("renders binary groups with the shared A/B palette and interval summary", () => {
  render(
    <DiagnosticCharts
      metricType="binary"
      diagnostics={{
        groups: ["A", "B"],
        proportions: [0.1, 0.14],
        ci_lower: [0.08, 0.11],
        ci_upper: [0.12, 0.17],
        counts: [1000, 1000],
        successes: [100, 140]
      }}
    />
  );

  const chart = screen.getByTestId("plotly-chart");
  expect(chart).toHaveAttribute("data-marker-color", "#27728a,#a35c35");
  expect(screen.getByText(/Error bars show confidence intervals/)).toBeInTheDocument();
});

it("renders all continuous diagnostic charts and their textual summaries", () => {
  const groupData = {
    histograms: {
      A: { bin_edges: [1, 2, 3], counts: [1, 2] },
      B: { bin_edges: [2, 3, 4], counts: [2, 1] }
    },
    boxplots: {
      A: { minimum: 1, q1: 1.5, median: 2, q3: 2.5, maximum: 3 },
      B: { minimum: 2, q1: 2.5, median: 3, q3: 3.5, maximum: 4 }
    },
    qq_plots: {
      A: { theoretical_quantiles: [-1, 0, 1], sample_quantiles: [1, 2, 3] },
      B: { theoretical_quantiles: [-1, 0, 1], sample_quantiles: [2, 3, 4] }
    }
  };

  render(<DiagnosticCharts metricType="continuous" diagnostics={groupData} />);

  expect(screen.getAllByTestId("plotly-chart")).toHaveLength(3);
  expect(screen.getByText("Histograms")).toBeInTheDocument();
  expect(screen.getByText("Boxplot summaries")).toBeInTheDocument();
  expect(screen.getByText("Normal QQ plots")).toBeInTheDocument();
  expect(screen.getByText(/near-linear point pattern/)).toBeInTheDocument();
  expect(screen.getAllByTestId("plotly-chart")[0]).toHaveAttribute("data-grid-color", "#e2e8ea");
  expect(screen.getAllByTestId("plotly-chart")[0]).toHaveAttribute("data-marker-color", "#27728a");
  expect(screen.getAllByTestId("plotly-chart")[0]).toHaveAttribute("data-responsive", "true");
});
