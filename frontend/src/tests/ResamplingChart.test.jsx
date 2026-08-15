import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ResamplingChart from "../components/ResamplingChart.jsx";

vi.mock("react-plotly.js", () => ({
  default: ({ config, data, layout }) => (
    <div
      data-testid="plotly-chart"
      data-points={data[0].x.length}
      data-lines={layout.shapes.length}
      data-grid-color={layout.yaxis.gridcolor}
      data-responsive={config.responsive}
    >
      {layout.title.text}
    </div>
  )
}));

afterEach(cleanup);

describe("ResamplingChart", () => {
  it("renders a permutation null distribution and observed-statistic marker", () => {
    render(
      <ResamplingChart
        result={{
          test_name: "permutation_mean_test",
          statistic: 1.5,
          metadata: { null_distribution: [-1, 0, 1, 2] }
        }}
      />
    );

    const chart = screen.getByTestId("plotly-chart");
    expect(chart).toHaveAttribute("data-points", "4");
    expect(chart).toHaveAttribute("data-lines", "1");
    expect(chart).toHaveAttribute("data-grid-color", "#e2e8ea");
    expect(chart).toHaveAttribute("data-responsive", "true");
    expect(screen.getByText(/4 permutations under H0/)).toBeInTheDocument();
    expect(screen.getByText(/observed B - A mean difference is 1.5000/)).toBeInTheDocument();
  });

  it("renders a bootstrap distribution with estimate and interval markers", () => {
    render(
      <ResamplingChart
        result={{
          test_name: "bootstrap_median_difference",
          estimate: 2,
          confidence_interval: { lower: 0.5, upper: 3.5, level: 0.95 },
          metadata: { bootstrap_distribution: [0.5, 1, 2, 3, 3.5] }
        }}
      />
    );

    const chart = screen.getByTestId("plotly-chart");
    expect(chart).toHaveAttribute("data-points", "5");
    expect(chart).toHaveAttribute("data-lines", "3");
    expect(screen.getByText(/5 bootstrap resamples/)).toBeInTheDocument();
    expect(screen.getByText(/95% percentile interval is \[0.5000, 3.5000\]/)).toBeInTheDocument();
  });

  it("renders nothing for a non-resampling analysis", () => {
    const { container } = render(
      <ResamplingChart result={{ test_name: "welch_t_test", metadata: {} }} />
    );

    expect(container).toBeEmptyDOMElement();
  });
});
