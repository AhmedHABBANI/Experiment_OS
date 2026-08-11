import { useState } from "react";

import { previewCsvDataset, validateCsvDataset } from "../api/datasets.js";

const initialMapping = {
  group_column: "",
  group_a_value: "",
  group_b_value: "",
  metric_column: "",
  metric_type: "continuous",
  binary_success_value: "",
  binary_failure_value: "",
  delimiter: ""
};

export default function CsvImportPanel({ onValidated }) {
  const [file, setFile] = useState(null);
  const [delimiter, setDelimiter] = useState("");
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState(initialMapping);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  async function handlePreview(event) {
    event.preventDefault();
    if (!file) {
      setError("Select a CSV file first.");
      return;
    }
    setStatus("previewing");
    setError("");
    try {
      const payload = await previewCsvDataset(file, delimiter);
      const firstColumn = payload.columns[0]?.name ?? "";
      const secondColumn = payload.columns[1]?.name ?? "";
      setPreview(payload);
      setMapping({
        ...initialMapping,
        delimiter: payload.delimiter,
        group_column: firstColumn,
        metric_column: secondColumn
      });
      setStatus("ready");
    } catch (caughtError) {
      setPreview(null);
      setError(caughtError.message);
      setStatus("error");
    }
  }

  async function handleValidate(event) {
    event.preventDefault();
    setStatus("validating");
    setError("");
    try {
      const payload = await validateCsvDataset(file, mapping);
      await onValidated(payload);
      setStatus("validated");
    } catch (caughtError) {
      setError(caughtError.message);
      setStatus("error");
    }
  }

  const columns = preview?.columns ?? [];

  return (
    <div className="csv-import">
      <form className="tool-panel" onSubmit={handlePreview}>
        <h2>CSV import</h2>
        <label className="field">
          <span>CSV file</span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setPreview(null);
              setError("");
            }}
          />
        </label>
        <label className="field">
          <span>Delimiter</span>
          <select value={delimiter} onChange={(event) => setDelimiter(event.target.value)}>
            <option value="">Detect automatically</option>
            <option value=",">Comma</option>
            <option value=";">Semicolon</option>
            <option value="\t">Tab</option>
            <option value="|">Pipe</option>
          </select>
        </label>
        <button className="primary-action" type="submit" disabled={status === "previewing"}>
          {status === "previewing" ? "Reading..." : "Preview CSV"}
        </button>
        {error ? <p className="error-message" role="alert">{error}</p> : null}
      </form>

      {preview ? (
        <>
          <section className="csv-preview" aria-label="CSV preview">
            <div className="result-header">
              <div>
                <p className="eyebrow">{preview.delimiter === "\t" ? "tab" : preview.delimiter} separated</p>
                <h2>{preview.filename}</h2>
              </div>
              <strong>{preview.row_count} rows</strong>
            </div>
            <div className="table-scroll">
              <table className="preview-table">
                <thead><tr>{columns.map((column) => <th key={column.name}>{column.name}</th>)}</tr></thead>
                <tbody>
                  {preview.preview_rows.map((row, index) => (
                    <tr key={index}>{columns.map((column) => <td key={column.name}>{formatCell(row[column.name])}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="column-summary">
              {columns.map((column) => (
                <span key={column.name}><strong>{column.name}</strong> {column.inferred_type}, {column.missing_count} missing</span>
              ))}
            </div>
          </section>

          <form className="mapping-panel" onSubmit={handleValidate}>
            <div className="section-heading"><p className="eyebrow">mapping</p><h2>Map the experiment</h2></div>
            <SelectField label="Group column" name="group_column" value={mapping.group_column} columns={columns} onChange={setMapping} />
            <TextField label="Group A value" name="group_a_value" value={mapping.group_a_value} onChange={setMapping} />
            <TextField label="Group B value" name="group_b_value" value={mapping.group_b_value} onChange={setMapping} />
            <SelectField label="Metric column" name="metric_column" value={mapping.metric_column} columns={columns} onChange={setMapping} />
            <label className="field">
              <span>Metric type</span>
              <select value={mapping.metric_type} onChange={(event) => setMapping((current) => ({ ...current, metric_type: event.target.value }))}>
                <option value="continuous">Continuous</option><option value="binary">Binary</option>
              </select>
            </label>
            {mapping.metric_type === "binary" ? (
              <>
                <TextField label="Success value (1)" name="binary_success_value" value={mapping.binary_success_value} onChange={setMapping} />
                <TextField label="Failure value (0)" name="binary_failure_value" value={mapping.binary_failure_value} onChange={setMapping} />
              </>
            ) : null}
            <button className="primary-action" type="submit" disabled={status === "validating"}>
              {status === "validating" ? "Validating..." : "Validate dataset"}
            </button>
          </form>
        </>
      ) : null}
    </div>
  );
}

function SelectField({ label, name, value, columns, onChange }) {
  return <label className="field"><span>{label}</span><select value={value} onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))}>{columns.map((column) => <option key={column.name} value={column.name}>{column.name}</option>)}</select></label>;
}

function TextField({ label, name, value, onChange }) {
  return <label className="field"><span>{label}</span><input required value={value} onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))} /></label>;
}

function formatCell(value) {
  return value === null || value === undefined ? "" : String(value);
}
