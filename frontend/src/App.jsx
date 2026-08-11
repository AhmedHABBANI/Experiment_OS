import { useMemo, useState } from "react";

import { analyzeBinaryExperiment } from "./api/analyses.js";
import { summarizeBinaryExperiment, summarizeContinuousExperiment } from "./api/descriptive.js";
import { fetchBinaryDiagnostics, fetchContinuousDiagnostics } from "./api/diagnostics.js";
import { simulateBinaryExperiment, simulateContinuousExperiment } from "./api/simulations.js";
import AnalysisResult from "./components/AnalysisResult.jsx";
import DiagnosticCharts from "./components/DiagnosticCharts.jsx";
import { downloadCsv, simulationToCsv } from "./lib/csv.js";

const initialBinaryForm = {
  n_a: 100,
  n_b: 100,
  p_a: 0.1,
  p_b: 0.12,
  seed: 42,
  missing_rate: 0
};

const initialContinuousForm = {
  n_a: 100,
  n_b: 100,
  mean_a: 10,
  mean_b: 11,
  std_a: 2,
  std_b: 2.5,
  distribution: "normal",
  seed: 42,
  missing_rate: 0,
  outlier_rate: 0,
  outlier_multiplier: 6
};

const initialBinaryAnalysis = {
  test: "two-proportion-z",
  alternative: "two-sided",
  alpha: 0.05
};

export default function App() {
  const [mode, setMode] = useState("binary");
  const [binaryForm, setBinaryForm] = useState(initialBinaryForm);
  const [continuousForm, setContinuousForm] = useState(initialContinuousForm);
  const [binaryAnalysis, setBinaryAnalysis] = useState(initialBinaryAnalysis);
  const [result, setResult] = useState(null);
  const [descriptiveSummary, setDescriptiveSummary] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const activeForm = mode === "binary" ? binaryForm : continuousForm;
  const previewRows = useMemo(() => buildPreviewRows(result), [result]);

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setError("");

    try {
      const payload =
        mode === "binary"
          ? await simulateBinaryExperiment(binaryForm)
          : await simulateContinuousExperiment(continuousForm);
      const [summary, diagnosticData, statisticalAnalysis] = await Promise.all(
        mode === "binary"
          ? [
              summarizeBinaryExperiment(payload),
              fetchBinaryDiagnostics(payload),
              analyzeBinaryExperiment(payload, binaryAnalysis)
            ]
          : [summarizeContinuousExperiment(payload), fetchContinuousDiagnostics(payload), null]
      );
      setResult(payload);
      setDescriptiveSummary(summary);
      setDiagnostics(diagnosticData);
      setAnalysisResult(statisticalAnalysis);
      setStatus("success");
    } catch (caughtError) {
      setResult(null);
      setDescriptiveSummary(null);
      setDiagnostics(null);
      setAnalysisResult(null);
      setError(caughtError.message);
      setStatus("error");
    }
  }

  function handleDownload() {
    if (!result) {
      return;
    }

    downloadCsv(`experiment-os-${result.metric_type}-simulation.csv`, simulationToCsv(result));
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-labelledby="page-title">
        <div className="page-heading">
          <div>
            <p className="eyebrow">ExperimentOS</p>
            <h1 id="page-title">Simulation workspace</h1>
          </div>
          <div className="mode-toggle" aria-label="Metric type">
            <button
              className={mode === "binary" ? "active" : ""}
              type="button"
              onClick={() => {
                setMode("binary");
                setResult(null);
                setDescriptiveSummary(null);
                setDiagnostics(null);
                setAnalysisResult(null);
              }}
            >
              Binary
            </button>
            <button
              className={mode === "continuous" ? "active" : ""}
              type="button"
              onClick={() => {
                setMode("continuous");
                setResult(null);
                setDescriptiveSummary(null);
                setDiagnostics(null);
                setAnalysisResult(null);
              }}
            >
              Continuous
            </button>
          </div>
        </div>

        <div className="content-grid">
          <form className="tool-panel" onSubmit={handleSubmit}>
            {mode === "binary" ? (
              <BinaryFields
                form={binaryForm}
                onChange={setBinaryForm}
                analysis={binaryAnalysis}
                onAnalysisChange={setBinaryAnalysis}
              />
            ) : (
              <ContinuousFields form={continuousForm} onChange={setContinuousForm} />
            )}

            <button className="primary-action" type="submit" disabled={status === "loading"}>
              {status === "loading" ? "Running..." : "Run simulation"}
            </button>
          </form>

          <section className="result-panel" aria-label="Simulation result">
            {status === "error" ? <p className="error-message">{error}</p> : null}
            {!result ? (
              <div className="empty-state">
                <h2>Dataset preview</h2>
                <p>Run a simulation to inspect the first rows and download the generated data.</p>
              </div>
            ) : (
              <>
                <div className="result-header">
                  <div>
                    <p className="eyebrow">{result.metric_type}</p>
                    <h2>Generated dataset</h2>
                  </div>
                  <button type="button" className="secondary-action" onClick={handleDownload}>
                    Download CSV
                  </button>
                </div>
                <MetadataGrid metadata={result.metadata} />
                {descriptiveSummary ? <DescriptiveSummary summary={descriptiveSummary} /> : null}
                {analysisResult ? <AnalysisResult result={analysisResult} /> : null}
                {diagnostics ? (
                  <DiagnosticCharts metricType={result.metric_type} diagnostics={diagnostics} />
                ) : null}
                <PreviewTable rows={previewRows} />
              </>
            )}
          </section>
        </div>

        <p className="footer-note">
          Current parameters: {Object.entries(activeForm).length} fields configured locally.
        </p>
      </section>
    </main>
  );
}

function BinaryFields({ form, onChange, analysis, onAnalysisChange }) {
  return (
    <>
      <h2>Binary simulation</h2>
      <NumberField label="Group A size" name="n_a" value={form.n_a} onChange={onChange} />
      <NumberField label="Group B size" name="n_b" value={form.n_b} onChange={onChange} />
      <NumberField label="P(A success)" name="p_a" value={form.p_a} step="0.01" onChange={onChange} />
      <NumberField label="P(B success)" name="p_b" value={form.p_b} step="0.01" onChange={onChange} />
      <NumberField label="Seed" name="seed" value={form.seed} onChange={onChange} />
      <NumberField
        label="Missing rate"
        name="missing_rate"
        value={form.missing_rate}
        step="0.01"
        onChange={onChange}
      />
      <div className="form-divider" />
      <h3>Analysis settings</h3>
      <label className="field">
        <span>Test</span>
        <select
          value={analysis.test}
          onChange={(event) => onAnalysisChange({ ...analysis, test: event.target.value })}
        >
          <option value="two-proportion-z">Two-proportion z-test</option>
          <option value="fisher-exact">Fisher exact test</option>
        </select>
      </label>
      <label className="field">
        <span>Alternative</span>
        <select
          value={analysis.alternative}
          onChange={(event) => onAnalysisChange({ ...analysis, alternative: event.target.value })}
        >
          <option value="two-sided">Two-sided</option>
          <option value="greater">B greater than A</option>
          <option value="less">B less than A</option>
        </select>
      </label>
      <NumberField label="Alpha" name="alpha" value={analysis.alpha} step="0.01" onChange={onAnalysisChange} />
    </>
  );
}

function ContinuousFields({ form, onChange }) {
  return (
    <>
      <h2>Continuous simulation</h2>
      <label className="field">
        <span>Distribution</span>
        <select
          value={form.distribution}
          onChange={(event) => onChange({ ...form, distribution: event.target.value })}
        >
          <option value="normal">Normal</option>
          <option value="exponential">Exponential</option>
          <option value="lognormal">Lognormal</option>
        </select>
      </label>
      <NumberField label="Group A size" name="n_a" value={form.n_a} onChange={onChange} />
      <NumberField label="Group B size" name="n_b" value={form.n_b} onChange={onChange} />
      <NumberField label="Mean A" name="mean_a" value={form.mean_a} step="0.1" onChange={onChange} />
      <NumberField label="Mean B" name="mean_b" value={form.mean_b} step="0.1" onChange={onChange} />
      <NumberField label="Std A" name="std_a" value={form.std_a} step="0.1" onChange={onChange} />
      <NumberField label="Std B" name="std_b" value={form.std_b} step="0.1" onChange={onChange} />
      <NumberField label="Seed" name="seed" value={form.seed} onChange={onChange} />
      <NumberField label="Missing rate" name="missing_rate" value={form.missing_rate} step="0.01" onChange={onChange} />
      <NumberField label="Outlier rate" name="outlier_rate" value={form.outlier_rate} step="0.01" onChange={onChange} />
      <NumberField
        label="Outlier multiplier"
        name="outlier_multiplier"
        value={form.outlier_multiplier}
        step="0.1"
        onChange={onChange}
      />
    </>
  );
}

function NumberField({ label, name, value, onChange, step = "1" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        name={name}
        type="number"
        step={step}
        value={value}
        onChange={(event) => onChange((current) => ({ ...current, [name]: Number(event.target.value) }))}
      />
    </label>
  );
}

function MetadataGrid({ metadata }) {
  const entries = Object.entries(metadata).filter(([, value]) => value !== null);

  return (
    <dl className="metadata-grid">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function DescriptiveSummary({ summary }) {
  const isBinary = summary.metric_type === "binary";
  const groupMetrics = isBinary
    ? [
        ["n", "n"],
        ["successes", "successes"],
        ["failures", "failures"],
        ["proportion", "proportion"],
        ["standard_error", "standard error"]
      ]
    : [
        ["n", "n"],
        ["mean", "mean"],
        ["median", "median"],
        ["standard_deviation", "std dev"],
        ["standard_error", "standard error"],
        ["iqr", "IQR"]
      ];
  const comparisonMetrics = isBinary
    ? [
        ["absolute_difference", "absolute difference"],
        ["relative_uplift", "relative uplift"],
        ["odds_ratio", "odds ratio"],
        ["risk_ratio", "risk ratio"]
      ]
    : [
        ["mean_difference", "mean difference"],
        ["median_difference", "median difference"],
        ["mean_ratio", "mean ratio"]
      ];

  return (
    <section className="summary-section" aria-label="Descriptive statistics">
      <div className="section-heading">
        <p className="eyebrow">descriptive</p>
        <h3>Group summaries</h3>
      </div>
      <div className="summary-grid">
        <SummaryCard title="Group A" values={summary.group_a} metrics={groupMetrics} />
        <SummaryCard title="Group B" values={summary.group_b} metrics={groupMetrics} />
        <SummaryCard title="Comparison" values={summary.comparison} metrics={comparisonMetrics} />
      </div>
    </section>
  );
}

function SummaryCard({ title, values, metrics }) {
  return (
    <article className="summary-card">
      <h4>{title}</h4>
      <dl>
        {metrics.map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>{formatMetricValue(values[key])}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

function PreviewTable({ rows }) {
  return (
    <table className="preview-table">
      <thead>
        <tr>
          <th>Row</th>
          <th>Group A</th>
          <th>Group B</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.index}>
            <td>{row.index}</td>
            <td>{formatPreviewValue(row.groupA)}</td>
            <td>{formatPreviewValue(row.groupB)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function buildPreviewRows(result) {
  if (!result) {
    return [];
  }

  const maxRows = Math.min(12, Math.max(result.group_a.length, result.group_b.length));

  return Array.from({ length: maxRows }, (_, index) => ({
    index: index + 1,
    groupA: result.group_a[index],
    groupB: result.group_b[index]
  }));
}

function formatPreviewValue(value) {
  if (value === null || value === undefined) {
    return "";
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(4);
}

function formatMetricValue(value) {
  if (value === null || value === undefined) {
    return "not defined";
  }

  if (typeof value !== "number") {
    return String(value);
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(4);
}
