import Plot from "react-plotly.js";

import { axisLayout, BASE_LAYOUT, CHART_COLORS, PLOT_CONFIG } from "./plotTheme.js";

export default function ResamplingChart({ result }) {
  if (result.test_name === "permutation_mean_test") {
    return <PermutationChart result={result} />;
  }

  if (
    result.test_name === "bootstrap_mean_difference" ||
    result.test_name === "bootstrap_median_difference"
  ) {
    return <BootstrapChart result={result} />;
  }

  return null;
}

function PermutationChart({ result }) {
  const distribution = result.metadata.null_distribution;

  return (
    <ChartSection
      title="Permutation null distribution"
      summary={`${distribution.length} permutations under H0. The observed B - A mean difference is ${formatValue(result.statistic)}.`}
    >
      <Plot
        data={[
          {
            type: "histogram",
            x: distribution,
            marker: { color: CHART_COLORS.groupA, line: { color: "#ffffff", width: 0.4 } },
            opacity: 0.82,
            hovertemplate: "Difference: %{x:.4f}<br>Count: %{y}<extra></extra>"
          }
        ]}
        layout={{
          ...BASE_LAYOUT,
          title: { ...BASE_LAYOUT.title, text: "Null distribution" },
          bargap: 0.04,
          xaxis: axisLayout({ title: "Permuted mean difference (B - A)" }),
          yaxis: axisLayout({ title: "Frequency", rangemode: "tozero" }),
          shapes: [verticalLine(result.statistic, CHART_COLORS.danger)],
          annotations: [lineLabel(result.statistic, "Observed", CHART_COLORS.danger)]
        }}
        config={PLOT_CONFIG}
        className="plot"
        useResizeHandler
      />
    </ChartSection>
  );
}

function BootstrapChart({ result }) {
  const distribution = result.metadata.bootstrap_distribution;
  const { lower, upper, level } = result.confidence_interval;

  return (
    <ChartSection
      title="Bootstrap distribution"
      summary={`${distribution.length} bootstrap resamples. The B - A estimate is ${formatValue(result.estimate)} and the ${formatPercent(level)} percentile interval is [${formatValue(lower)}, ${formatValue(upper)}].`}
    >
      <Plot
        data={[
          {
            type: "histogram",
            x: distribution,
            marker: { color: CHART_COLORS.groupB, line: { color: "#ffffff", width: 0.4 } },
            opacity: 0.82,
            hovertemplate: "Difference: %{x:.4f}<br>Count: %{y}<extra></extra>"
          }
        ]}
        layout={{
          ...BASE_LAYOUT,
          title: { ...BASE_LAYOUT.title, text: "Bootstrap estimates" },
          bargap: 0.04,
          xaxis: axisLayout({ title: "Resampled difference (B - A)" }),
          yaxis: axisLayout({ title: "Frequency", rangemode: "tozero" }),
          shapes: [
            verticalLine(lower, CHART_COLORS.interval, "dot"),
            verticalLine(result.estimate, CHART_COLORS.ink),
            verticalLine(upper, CHART_COLORS.interval, "dot")
          ],
          annotations: [
            lineLabel(lower, "Lower", CHART_COLORS.interval),
            lineLabel(result.estimate, "Estimate", CHART_COLORS.ink),
            lineLabel(upper, "Upper", CHART_COLORS.interval)
          ]
        }}
        config={PLOT_CONFIG}
        className="plot"
        useResizeHandler
      />
    </ChartSection>
  );
}

function ChartSection({ title, summary, children }) {
  return (
    <section className="resampling-section" aria-label="Resampling distribution">
      <div className="section-heading">
        <p className="eyebrow">resampling</p>
        <h3>{title}</h3>
      </div>
      <div className="chart-panel">
        {children}
        <p className="chart-summary">{summary}</p>
      </div>
    </section>
  );
}

function verticalLine(value, color, dash = "solid") {
  return {
    type: "line",
    x0: value,
    x1: value,
    xref: "x",
    y0: 0,
    y1: 1,
    yref: "paper",
    line: { color, width: 2, dash }
  };
}

function lineLabel(value, text, color) {
  return {
    x: value,
    y: 1,
    xref: "x",
    yref: "paper",
    text,
    showarrow: false,
    yanchor: "bottom",
    font: { color, size: 11 }
  };
}

function formatValue(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(4);
}

function formatPercent(value) {
  return new Intl.NumberFormat("en", { style: "percent", maximumFractionDigits: 1 }).format(value);
}
