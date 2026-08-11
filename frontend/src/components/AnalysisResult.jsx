export default function AnalysisResult({ result }) {
  const metrics = [
    ["statistic", "statistic"],
    ["p_value", "p-value"],
    ["estimate", "B - A estimate"],
    ["effect_size", result.effect_size_name ?? "effect size"]
  ];

  return (
    <section className="analysis-section" aria-label="Statistical analysis">
      <div className="analysis-heading">
        <div>
          <p className="eyebrow">analysis</p>
          <h3>Statistical analysis</h3>
        </div>
        <span className={`decision-badge ${result.reject_null ? "reject" : "retain"}`}>
          {result.reject_null ? "Reject H0" : "Do not reject H0"}
        </span>
      </div>

      <p className="analysis-method">{formatTestName(result.test_name)}</p>

      <dl className="analysis-metrics">
        {metrics.map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>{formatValue(result[key])}</dd>
          </div>
        ))}
      </dl>

      {result.confidence_interval ? (
        <p className="interval-summary">
          {formatPercent(result.confidence_interval.level)} confidence interval: [
          {formatValue(result.confidence_interval.lower)}, {formatValue(result.confidence_interval.upper)}]
        </p>
      ) : null}

      <div className="hypotheses">
        <p>
          <strong>H0</strong> {result.interpretation.null_hypothesis}
        </p>
        <p>
          <strong>H1</strong> {result.interpretation.alternative_hypothesis}
        </p>
      </div>

      {result.warnings.length > 0 ? (
        <div className="warning-list" aria-label="Statistical warnings">
          {result.warnings.map((warning) => (
            <p key={warning.code}>
              <strong>{warning.code}</strong> {warning.message}
            </p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function formatTestName(testName) {
  return testName
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function formatValue(value) {
  if (value === null || value === undefined) {
    return "not defined";
  }

  if (Math.abs(value) > 0 && Math.abs(value) < 0.0001) {
    return value.toExponential(3);
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(4);
}

function formatPercent(value) {
  return new Intl.NumberFormat("en", { style: "percent", maximumFractionDigits: 1 }).format(value);
}
