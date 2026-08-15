import { lazy, Suspense, useMemo, useState } from "react";

import { analyzeBinaryExperiment, analyzeContinuousExperiment } from "./api/analyses.js";
import { summarizeBinaryExperiment, summarizeContinuousExperiment } from "./api/descriptive.js";
import { fetchBinaryDiagnostics, fetchContinuousDiagnostics } from "./api/diagnostics.js";
import {
  exportAnalyzedDataCsv,
  exportJsonReport,
  exportPdfReport,
  exportResultsCsv
} from "./api/exports.js";
import { simulateBinaryExperiment, simulateContinuousExperiment } from "./api/simulations.js";
import AnalysisResult from "./components/AnalysisResult.jsx";
import CsvImportPanel from "./components/CsvImportPanel.jsx";
import { downloadCsv } from "./lib/csv.js";
import { downloadJson } from "./lib/json.js";
import { downloadPdf } from "./lib/pdf.js";

const DiagnosticCharts = lazy(() => import("./components/DiagnosticCharts.jsx"));
const ResamplingChart = lazy(() => import("./components/ResamplingChart.jsx"));

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

const initialContinuousAnalysis = {
  test: "student-t",
  alternative: "two-sided",
  alpha: 0.05,
  n_permutations: 1000,
  estimand: "mean",
  confidence_level: 0.95,
  n_resamples: 1000,
  seed: 42
};

export default function App() {
  const [source, setSource] = useState("simulation");
  const [mode, setMode] = useState("binary");
  const [binaryForm, setBinaryForm] = useState(initialBinaryForm);
  const [continuousForm, setContinuousForm] = useState(initialContinuousForm);
  const [binaryAnalysis, setBinaryAnalysis] = useState(initialBinaryAnalysis);
  const [continuousAnalysis, setContinuousAnalysis] = useState(initialContinuousAnalysis);
  const [result, setResult] = useState(null);
  const [descriptiveSummary, setDescriptiveSummary] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const activeForm = mode === "binary" ? binaryForm : continuousForm;
  const previewRows = useMemo(() => buildPreviewRows(result), [result]);

  function resetResults() {
    setResult(null);
    setDescriptiveSummary(null);
    setDiagnostics(null);
    setAnalysisResult(null);
    setError("");
    setStatus("idle");
  }

  async function processDataset(payload) {
    const continuousMinimumSize = continuousAnalysis.test === "mann-whitney" ? 1 : 2;
    const canRunContinuousAnalysis =
      payload.metric_type === "continuous" &&
      payload.group_a.length >= continuousMinimumSize &&
      payload.group_b.length >= continuousMinimumSize;
    const [summary, diagnosticData, statisticalAnalysis] = await Promise.all(
      payload.metric_type === "binary"
        ? [
            summarizeBinaryExperiment(payload),
            fetchBinaryDiagnostics(payload),
            analyzeBinaryExperiment(payload, binaryAnalysis)
          ]
        : [
            summarizeContinuousExperiment(payload),
            fetchContinuousDiagnostics(payload),
            canRunContinuousAnalysis
              ? analyzeContinuousExperiment(payload, continuousAnalysis)
              : null
          ]
    );
    setMode(payload.metric_type);
    setResult(payload);
    setDescriptiveSummary(summary);
    setDiagnostics(diagnosticData);
    setAnalysisResult(statisticalAnalysis);
    setStatus("success");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setError("");

    try {
      const payload =
        mode === "binary"
          ? await simulateBinaryExperiment(binaryForm)
          : await simulateContinuousExperiment(continuousForm);
      await processDataset(payload);
    } catch (caughtError) {
      setResult(null);
      setDescriptiveSummary(null);
      setDiagnostics(null);
      setAnalysisResult(null);
      setError(caughtError.message);
      setStatus("error");
    }
  }

  async function handleImportedDataset(payload) {
    setStatus("loading");
    setError("");
    try {
      await processDataset(payload);
    } catch (caughtError) {
      resetResults();
      setError(caughtError.message);
      setStatus("error");
      throw caughtError;
    }
  }

  async function handleDownload() {
    if (!result) {
      return;
    }

    setError("");
    try {
      const content = await exportAnalyzedDataCsv(result);
      downloadCsv("experiment-os-analyzed-data.csv", content);
    } catch (caughtError) {
      setError(caughtError.message);
    }
  }

  async function handleJsonExport() {
    if (!result || !descriptiveSummary || !analysisResult) {
      return;
    }

    setError("");
    try {
      const content = await exportJsonReport(buildReportPayload());
      downloadJson("experiment-os-report.json", content);
    } catch (caughtError) {
      setError(caughtError.message);
    }
  }

  async function handleResultsCsvExport() {
    if (!result || !descriptiveSummary || !analysisResult) {
      return;
    }

    setError("");
    try {
      const content = await exportResultsCsv(buildReportPayload());
      downloadCsv("experiment-os-results.csv", content);
    } catch (caughtError) {
      setError(caughtError.message);
    }
  }

  async function handlePdfExport() {
    if (!result || !descriptiveSummary || !analysisResult) {
      return;
    }

    setError("");
    try {
      const content = await exportPdfReport(buildReportPayload());
      downloadPdf("experiment-os-report.pdf", content);
    } catch (caughtError) {
      setError(caughtError.message);
    }
  }

  function buildReportPayload() {
    return {
      source: result.metadata?.source === "csv_import" ? "csv_import" : "simulation",
      configuration: {
        simulation: source === "simulation" ? activeForm : null,
        analysis: mode === "binary" ? binaryAnalysis : continuousAnalysis
      },
      dataset: result,
      descriptive_summary: descriptiveSummary,
      analysis_result: analysisResult
    };
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-labelledby="page-title">
        <header className="product-header">
          <div className="product-brand">
            <span className="brand-mark" aria-hidden="true">OS</span>
            <div>
              <strong>ExperimentOS</strong>
              <span>Frequentist A/B analysis</span>
            </div>
          </div>
          <div className="product-status" aria-label="Application status">
            <span><i className="status-dot" aria-hidden="true" />Local workspace</span>
            <span>Session only</span>
          </div>
        </header>

        <div className="page-heading">
          <div>
            <p className="eyebrow">Analysis workspace</p>
            <h1 id="page-title">Experiment workspace</h1>
            <p className="page-description">Configure, analyze and interpret one A/B metric at a time.</p>
          </div>
          <div className="mode-toggle" aria-label="Data source">
            <button
              aria-pressed={source === "simulation"}
              className={source === "simulation" ? "active" : ""}
              type="button"
              onClick={() => {
                setSource("simulation");
                resetResults();
              }}
            >
              Simulate
            </button>
            <button
              aria-pressed={source === "csv"}
              className={source === "csv" ? "active" : ""}
              type="button"
              onClick={() => {
                setSource("csv");
                resetResults();
              }}
            >
              Import CSV
            </button>
          </div>
        </div>

        <div className="workspace-context" aria-label="Current experiment context">
          <span><strong>Source</strong>{source === "simulation" ? "Simulation" : "CSV import"}</span>
          <span><strong>Metric</strong>{mode === "binary" ? "Binary" : "Continuous"}</span>
          <span><strong>Direction</strong>B - A</span>
        </div>

        <div className="content-grid">
          {source === "simulation" ? (
            <form className="tool-panel" onSubmit={handleSubmit}>
              <div className="metric-toggle" aria-label="Metric type">
                <button aria-pressed={mode === "binary"} className={mode === "binary" ? "active" : ""} type="button" onClick={() => { setMode("binary"); resetResults(); }}>Binary</button>
                <button aria-pressed={mode === "continuous"} className={mode === "continuous" ? "active" : ""} type="button" onClick={() => { setMode("continuous"); resetResults(); }}>Continuous</button>
              </div>
              {mode === "binary" ? (
                <BinaryFields form={binaryForm} onChange={setBinaryForm} analysis={binaryAnalysis} onAnalysisChange={setBinaryAnalysis} />
              ) : (
                <ContinuousFields
                  form={continuousForm}
                  onChange={setContinuousForm}
                  analysis={continuousAnalysis}
                  onAnalysisChange={setContinuousAnalysis}
                />
              )}
              <button className="primary-action" type="submit" disabled={status === "loading"}>{status === "loading" ? "Running..." : "Run simulation"}</button>
            </form>
          ) : (
            <CsvImportPanel onValidated={handleImportedDataset} />
          )}

          <section className="result-panel" aria-label="Simulation result" aria-busy={status === "loading"}>
            <p className="sr-only" aria-live="polite">
              {status === "loading" ? "Experiment analysis is running." : ""}
            </p>
            {status === "error" ? <p className="error-message" role="alert">{error}</p> : null}
            {!result ? (
              <div className="empty-state">
                <h2>Dataset results</h2>
                <p>{source === "simulation" ? "Run a simulation to inspect and analyze the generated data." : "Preview and map a CSV to analyze the retained observations."}</p>
              </div>
            ) : (
              <>
                <div className="result-header">
                  <div>
                    <p className="eyebrow">{result.metric_type}</p>
                    <h2>{source === "simulation" ? "Generated dataset" : "Imported dataset"}</h2>
                  </div>
                  <div className="result-actions">
                    <span className="result-actions-label">Export</span>
                    <button type="button" className="secondary-action" onClick={handleDownload}>
                      Data CSV
                    </button>
                    {analysisResult ? (
                      <>
                        <button type="button" className="secondary-action" onClick={handleJsonExport}>
                          JSON
                        </button>
                        <button type="button" className="secondary-action" onClick={handleResultsCsvExport}>
                          Results CSV
                        </button>
                        <button type="button" className="secondary-action" onClick={handlePdfExport}>
                          PDF report
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
                <MetadataGrid metadata={result.metadata} />
                {result.metadata?.source === "csv_import" ? <ImportSummary metadata={result.metadata} /> : null}
                {descriptiveSummary ? <DescriptiveSummary summary={descriptiveSummary} /> : null}
                {analysisResult ? <AnalysisResult result={analysisResult} /> : null}
                <Suspense fallback={<p className="chart-loading" role="status">Loading charts...</p>}>
                  {analysisResult ? <ResamplingChart result={analysisResult} /> : null}
                  {diagnostics ? (
                    <DiagnosticCharts metricType={result.metric_type} diagnostics={diagnostics} />
                  ) : null}
                </Suspense>
                <PreviewTable rows={previewRows} />
              </>
            )}
          </section>
        </div>

        <p className="footer-note">No uploaded data is stored. {source === "simulation" ? `${Object.entries(activeForm).length} parameters are configured locally.` : "CSV processing remains in memory for this session."}</p>
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

function ContinuousFields({ form, onChange, analysis, onAnalysisChange }) {
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
      <div className="form-divider" />
      <h3>Analysis settings</h3>
      <label className="field">
        <span>Test</span>
        <select
          value={analysis.test}
          onChange={(event) =>
            onAnalysisChange({
              ...analysis,
              test: event.target.value,
              alternative:
                event.target.value === "mann-whitney" ? "two-sided" : analysis.alternative
            })
          }
        >
          <option value="student-t">Student t-test</option>
          <option value="welch-t">Welch t-test</option>
          <option value="mann-whitney">Mann-Whitney U test</option>
          <option value="permutation">Permutation mean test</option>
          <option value="bootstrap">Bootstrap difference</option>
        </select>
      </label>
      {analysis.test !== "bootstrap" ? (
        <>
          <label className="field">
            <span>Alternative</span>
            <select
              value={analysis.alternative}
              disabled={analysis.test === "mann-whitney"}
              onChange={(event) =>
                onAnalysisChange({ ...analysis, alternative: event.target.value })
              }
            >
              <option value="two-sided">Two-sided</option>
              <option value="greater">B greater than A</option>
              <option value="less">B less than A</option>
            </select>
          </label>
          <NumberField
            label="Alpha"
            name="alpha"
            value={analysis.alpha}
            step="0.01"
            onChange={onAnalysisChange}
          />
        </>
      ) : null}
      {analysis.test === "permutation" ? (
        <>
          <NumberField
            label="Permutations"
            name="n_permutations"
            value={analysis.n_permutations}
            min="100"
            max="100000"
            onChange={onAnalysisChange}
          />
          <OptionalNumberField
            label="Analysis seed"
            name="seed"
            value={analysis.seed}
            min="0"
            onChange={onAnalysisChange}
          />
        </>
      ) : null}
      {analysis.test === "bootstrap" ? (
        <>
          <label className="field">
            <span>Estimand</span>
            <select
              value={analysis.estimand}
              onChange={(event) =>
                onAnalysisChange({ ...analysis, estimand: event.target.value })
              }
            >
              <option value="mean">Mean difference</option>
              <option value="median">Median difference</option>
            </select>
          </label>
          <NumberField
            label="Resamples"
            name="n_resamples"
            value={analysis.n_resamples}
            min="100"
            max="100000"
            onChange={onAnalysisChange}
          />
          <NumberField
            label="Confidence level"
            name="confidence_level"
            value={analysis.confidence_level}
            min="0.01"
            max="0.99"
            step="0.01"
            onChange={onAnalysisChange}
          />
          <OptionalNumberField
            label="Analysis seed"
            name="seed"
            value={analysis.seed}
            min="0"
            onChange={onAnalysisChange}
          />
        </>
      ) : null}
    </>
  );
}

function NumberField({ label, name, value, onChange, step = "1", min, max }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        name={name}
        type="number"
        step={step}
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange((current) => ({ ...current, [name]: Number(event.target.value) }))}
      />
    </label>
  );
}

function OptionalNumberField({ label, name, value, onChange, step = "1", min, max }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        name={name}
        type="number"
        step={step}
        min={min}
        max={max}
        value={value ?? ""}
        onChange={(event) =>
          onChange((current) => ({
            ...current,
            [name]: event.target.value === "" ? null : Number(event.target.value)
          }))
        }
      />
    </label>
  );
}

function MetadataGrid({ metadata }) {
  const entries = Object.entries(metadata).filter(([, value]) => value !== null && typeof value !== "object");

  return (
    <dl className="metadata-grid">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{key.replaceAll("_", " ")}</dt>
          <dd>{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function ImportSummary({ metadata }) {
  const exclusions = Object.entries(metadata.exclusion_reasons ?? {}).filter(([, count]) => count > 0);
  return (
    <section className="import-summary" aria-label="Import validation summary">
      <h3>Import validation</h3>
      <dl>
        <div><dt>Group A retained</dt><dd>{metadata.validation?.group_a?.valid_size ?? 0}</dd></div>
        <div><dt>Group B retained</dt><dd>{metadata.validation?.group_b?.valid_size ?? 0}</dd></div>
        <div><dt>Rows excluded</dt><dd>{metadata.excluded_rows}</dd></div>
      </dl>
      {exclusions.length ? <p>{exclusions.map(([reason, count]) => `${reason.replaceAll("_", " ")}: ${count}`).join(" · ")}</p> : <p>No rows were excluded.</p>}
    </section>
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
