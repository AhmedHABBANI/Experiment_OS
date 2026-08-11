import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import DiagnosticCharts from "../components/DiagnosticCharts.jsx";

vi.mock("react-plotly.js", () => ({
  default: ({ layout }) => <div data-testid="plotly-chart">{layout.title.text}</div>
}));

afterEach(cleanup);

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
});
