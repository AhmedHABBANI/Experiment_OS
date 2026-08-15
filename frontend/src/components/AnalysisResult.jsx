export default function AnalysisResult({ result }) {
  const isEstimationOnly = result.reject_null === null;
  const decisionLabel = isEstimationOnly
    ? "Estimation only"
    : result.reject_null
      ? "Reject H0"
      : "Do not reject H0";
  const metrics = [
    ["estimate", "B - A estimate", "primary"],
    ["p_value", "p-value", "primary"],
    ["statistic", "test statistic", "secondary"],
    ["effect_size", result.effect_size_name ?? "effect size", "secondary"]
  ];

  return (
    <section className="analysis-section" aria-label="Statistical analysis">
      <div className={`decision-panel ${isEstimationOnly ? "estimate" : result.reject_null ? "reject" : "retain"}`}>
        <div>
          <p className="decision-kicker">Statistical decision</p>
          <h3>{decisionLabel}</h3>
          <p className="analysis-method">{formatTestName(result.test_name)}</p>
        </div>
        <span className="decision-threshold">
          {isEstimationOnly ? "Interval estimate" : `alpha ${formatValue(result.alpha)}`}
        </span>
      </div>

      <dl className="analysis-metrics">
        {metrics.map(([key, label, emphasis]) => (
          <div className={emphasis} key={key}>
            <dt>{label}</dt>
            <dd>{formatValue(result[key])}</dd>
          </div>
        ))}
      </dl>

      {result.confidence_interval ? (
        <div className="interval-summary">
          <span>{formatPercent(result.confidence_interval.level)} confidence interval</span>
          <strong>[{formatValue(result.confidence_interval.lower)}, {formatValue(result.confidence_interval.upper)}]</strong>
        </div>
      ) : null}

      <div className="analysis-detail-grid">
        <div className="hypotheses">
          <h4>Question and hypotheses</h4>
        {result.interpretation.question ? <p>{result.interpretation.question}</p> : null}
        <p>
            <strong>H0</strong><span>{result.interpretation.null_hypothesis}</span>
        </p>
        <p>
            <strong>H1</strong><span>{result.interpretation.alternative_hypothesis}</span>
        </p>
        </div>

        <div className="interpretation-summary" aria-label="Deterministic interpretation">
          <h4>Interpretation</h4>
        {[
          ["decision", "Decision"],
          ["effect", "Effect"],
          ["uncertainty", "Uncertainty"],
          ["practical_significance", "Practical significance"],
          ["warning_context", "Warning context"]
        ].map(([key, label]) =>
          result.interpretation[key] ? (
            <p key={key}>
                <strong>{label}</strong><span>{result.interpretation[key]}</span>
            </p>
          ) : null
        )}
        </div>
      </div>

      {result.warnings.length > 0 ? (
        <div className="warning-list" aria-label="Statistical warnings">
          <h4>Statistical cautions</h4>
          {result.warnings.map((warning) => (
            <p key={warning.code}>
              <strong>{warning.code.replaceAll("_", " ")}</strong>
              <span>{warning.message}</span>
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
