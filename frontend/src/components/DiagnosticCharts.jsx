import Plot from "react-plotly.js";

const colors = {
  A: "#176b87",
  B: "#c75b39"
};

const plotConfig = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ["lasso2d", "select2d"]
};

const baseLayout = {
  autosize: true,
  margin: { l: 52, r: 18, t: 42, b: 48 },
  paper_bgcolor: "#ffffff",
  plot_bgcolor: "#f8fbfc",
  font: { color: "#293943", family: "Inter, system-ui, sans-serif" },
  legend: { orientation: "h", y: 1.15 },
  hoverlabel: { bgcolor: "#18242c", font: { color: "#ffffff" } }
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
            marker: { color: diagnostics.groups.map((group) => colors[group]) },
            error_y: { type: "data", array: errorPlus, arrayminus: errorMinus, visible: true },
            customdata: diagnostics.groups.map((_, index) => [
              diagnostics.successes[index],
              diagnostics.counts[index]
            ]),
            hovertemplate: "%{x}: %{y:.2%}<br>%{customdata[0]}/%{customdata[1]} successes<extra></extra>"
          }
        ]}
        layout={{
          ...baseLayout,
          title: { text: "Observed success rates", font: { size: 15 } },
          yaxis: { title: "Success rate", tickformat: ".0%", rangemode: "tozero" },
          xaxis: { title: "Group" }
        }}
        config={plotConfig}
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
      marker: { color: colors[group] },
      opacity: 0.68,
      hovertemplate: `${group}: %{y} observations<extra></extra>`
    };
  });

  return (
    <ChartPanel summary="Overlapping bins make the shape and spread of both groups directly comparable.">
      <Plot
        data={traces}
        layout={{
          ...baseLayout,
          barmode: "overlay",
          title: { text: "Histograms", font: { size: 15 } },
          xaxis: { title: "Observed value" },
          yaxis: { title: "Count", rangemode: "tozero" }
        }}
        config={plotConfig}
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
    marker: { color: colors[group] },
    boxpoints: false
  }));

  return (
    <ChartPanel summary="The boxplots compare medians, interquartile ranges and observed extremes.">
      <Plot
        data={traces}
        layout={{
          ...baseLayout,
          title: { text: "Boxplot summaries", font: { size: 15 } },
          yaxis: { title: "Observed value" }
        }}
        config={plotConfig}
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
    marker: { color: colors[group], size: 6, opacity: 0.72 },
    hovertemplate: "Theoretical: %{x:.3f}<br>Observed: %{y:.3f}<extra></extra>"
  }));

  return (
    <ChartPanel summary="A near-linear point pattern is compatible with an approximately normal distribution.">
      <Plot
        data={traces}
        layout={{
          ...baseLayout,
          title: { text: "Normal QQ plots", font: { size: 15 } },
          xaxis: { title: "Theoretical normal quantile" },
          yaxis: { title: "Observed quantile" }
        }}
        config={plotConfig}
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
