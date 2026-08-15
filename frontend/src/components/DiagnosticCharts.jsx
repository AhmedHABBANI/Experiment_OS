import Plot from "react-plotly.js";

import { axisLayout, BASE_LAYOUT, CHART_COLORS, PLOT_CONFIG } from "./plotTheme.js";

const groupColors = {
  A: CHART_COLORS.groupA,
  B: CHART_COLORS.groupB
};

export default function DiagnosticCharts({ metricType, diagnostics }) {
  return (
    <section className="diagnostics-section" aria-label="Distribution diagnostics">
      <div className="section-heading">
        <p className="eyebrow">diagnostics</p>
        <h3>Distribution diagnostics</h3>
      </div>
      {metricType === "binary" ? (
        <BinaryRateChart diagnostics={diagnostics} />
      ) : (
        <ContinuousCharts diagnostics={diagnostics} />
      )}
    </section>
  );
}

function BinaryRateChart({ diagnostics }) {
  const errorMinus = diagnostics.proportions.map(
    (proportion, index) => proportion - diagnostics.ci_lower[index]
  );
  const errorPlus = diagnostics.proportions.map(
    (proportion, index) => diagnostics.ci_upper[index] - proportion
  );

  return (
    <div className="chart-panel">
      <Plot
        data={[
          {
            type: "bar",
            x: diagnostics.groups,
            y: diagnostics.proportions,
            marker: {
              color: diagnostics.groups.map((group) => groupColors[group]),
              line: { color: "#ffffff", width: 1 }
            },
            error_y: { type: "data", array: errorPlus, arrayminus: errorMinus, visible: true },
            customdata: diagnostics.groups.map((_, index) => [
              diagnostics.successes[index],
              diagnostics.counts[index]
            ]),
            hovertemplate: "%{x}: %{y:.2%}<br>%{customdata[0]}/%{customdata[1]} successes<extra></extra>"
          }
        ]}
        layout={{
          ...BASE_LAYOUT,
          title: { ...BASE_LAYOUT.title, text: "Observed success rates" },
          bargap: 0.48,
          yaxis: axisLayout({ title: "Success rate", tickformat: ".0%", rangemode: "tozero" }),
          xaxis: axisLayout({ title: "Experiment group", showgrid: false })
        }}
        config={PLOT_CONFIG}
        className="plot"
        useResizeHandler
      />
      <p className="chart-summary">
        Group A: {formatPercent(diagnostics.proportions[0])}; Group B:{" "}
        {formatPercent(diagnostics.proportions[1])}. Error bars show confidence intervals.
      </p>
    </div>
  );
}

function ContinuousCharts({ diagnostics }) {
  return (
    <div className="chart-grid">
      <HistogramChart histograms={diagnostics.histograms} />
      <BoxplotChart boxplots={diagnostics.boxplots} />
      <QQPlotChart qqPlots={diagnostics.qq_plots} />
    </div>
  );
}

function HistogramChart({ histograms }) {
  const traces = ["A", "B"].map((group) => {
    const histogram = histograms[group];
    const widths = histogram.bin_edges.slice(1).map((edge, index) => edge - histogram.bin_edges[index]);
    const centers = widths.map((width, index) => histogram.bin_edges[index] + width / 2);

    return {
      type: "bar",
      name: `Group ${group}`,
      x: centers,
      y: histogram.counts,
      width: widths,
      marker: { color: groupColors[group], line: { color: "#ffffff", width: 0.5 } },
      opacity: 0.62,
      hovertemplate: `Group ${group}<br>Center: %{x:.4f}<br>Count: %{y}<extra></extra>`
    };
  });

  return (
    <ChartPanel summary="Overlapping bins make the shape and spread of both groups directly comparable.">
      <Plot
        data={traces}
        layout={{
          ...BASE_LAYOUT,
          barmode: "overlay",
          title: { ...BASE_LAYOUT.title, text: "Histograms" },
          xaxis: axisLayout({ title: "Observed value" }),
          yaxis: axisLayout({ title: "Observations", rangemode: "tozero" })
        }}
        config={PLOT_CONFIG}
        className="plot"
        useResizeHandler
      />
    </ChartPanel>
  );
}

function BoxplotChart({ boxplots }) {
  const traces = ["A", "B"].map((group) => ({
    type: "box",
    name: `Group ${group}`,
    q1: [boxplots[group].q1],
    median: [boxplots[group].median],
    q3: [boxplots[group].q3],
    lowerfence: [boxplots[group].minimum],
    upperfence: [boxplots[group].maximum],
    marker: { color: groupColors[group] },
    line: { color: groupColors[group], width: 2 },
    fillcolor: groupColors[group],
    opacity: 0.72,
    boxpoints: false,
    hovertemplate: `Group ${group}<br>Value: %{y:.4f}<extra></extra>`
  }));

  return (
    <ChartPanel summary="The boxplots compare medians, interquartile ranges and observed extremes.">
      <Plot
        data={traces}
        layout={{
          ...BASE_LAYOUT,
          title: { ...BASE_LAYOUT.title, text: "Boxplot summaries" },
          xaxis: axisLayout({ showgrid: false }),
          yaxis: axisLayout({ title: "Observed value" })
        }}
        config={PLOT_CONFIG}
        className="plot"
        useResizeHandler
      />
    </ChartPanel>
  );
}

function QQPlotChart({ qqPlots }) {
  const traces = ["A", "B"].map((group) => ({
    type: "scatter",
    mode: "markers",
    name: `Group ${group}`,
    x: qqPlots[group].theoretical_quantiles,
    y: qqPlots[group].sample_quantiles,
    marker: {
      color: groupColors[group],
      size: 7,
      opacity: 0.76,
      line: { color: "#ffffff", width: 0.5 }
    },
    hovertemplate: `Group ${group}<br>Theoretical: %{x:.3f}<br>Observed: %{y:.3f}<extra></extra>`
  }));

  return (
    <ChartPanel summary="A near-linear point pattern is compatible with an approximately normal distribution.">
      <Plot
        data={traces}
        layout={{
          ...BASE_LAYOUT,
          title: { ...BASE_LAYOUT.title, text: "Normal QQ plots" },
          xaxis: axisLayout({ title: "Theoretical normal quantile" }),
          yaxis: axisLayout({ title: "Observed quantile" })
        }}
        config={PLOT_CONFIG}
        className="plot"
        useResizeHandler
      />
    </ChartPanel>
  );
}

function ChartPanel({ children, summary }) {
  return (
    <div className="chart-panel">
      {children}
      <p className="chart-summary">{summary}</p>
    </div>
  );
}

function formatPercent(value) {
  return new Intl.NumberFormat("en", { style: "percent", maximumFractionDigits: 2 }).format(value);
}
