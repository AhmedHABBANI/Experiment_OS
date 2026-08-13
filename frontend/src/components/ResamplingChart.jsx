import Plot from "react-plotly.js";

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
  hoverlabel: { bgcolor: "#18242c", font: { color: "#ffffff" } },
  yaxis: { title: "Count", rangemode: "tozero" }
};

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
            marker: { color: "#176b87" },
            opacity: 0.82,
            hovertemplate: "Difference: %{x:.4f}<br>Count: %{y}<extra></extra>"
          }
        ]}
        layout={{
          ...baseLayout,
          title: { text: "Null distribution", font: { size: 15 } },
          xaxis: { title: "Permuted mean difference (B - A)" },
          shapes: [verticalLine(result.statistic, "#a9422a")],
          annotations: [lineLabel(result.statistic, "Observed", "#7b2e17")]
        }}
        config={plotConfig}
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
            marker: { color: "#c75b39" },
            opacity: 0.82,
            hovertemplate: "Difference: %{x:.4f}<br>Count: %{y}<extra></extra>"
          }
        ]}
        layout={{
          ...baseLayout,
          title: { text: "Bootstrap estimates", font: { size: 15 } },
          xaxis: { title: "Resampled difference (B - A)" },
          shapes: [
            verticalLine(lower, "#176b87", "dot"),
            verticalLine(result.estimate, "#293943"),
            verticalLine(upper, "#176b87", "dot")
          ],
          annotations: [
            lineLabel(lower, "Lower", "#176b87"),
            lineLabel(result.estimate, "Estimate", "#293943"),
            lineLabel(upper, "Upper", "#176b87")
          ]
        }}
        config={plotConfig}
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
