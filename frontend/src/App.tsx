import React from "react";
import { useEffect, useMemo, useState } from "react";
import {
  FileText,
  Upload,
  Trash2,
  Download,
  CheckCircle2,
  AlertTriangle,
  Clock3,
  Activity,
  ChevronRight,
  BrainCircuit,
  RefreshCw,
} from "lucide-react";
import { api, DocumentRecord } from "./lib/api";
const human = (s: string) =>
  s.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const money = (v: unknown, currency?: unknown) =>
  typeof v === "number"
    ? typeof currency === "string" &&
      [
        "INR",
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CNY",
        "SGD",
        "AED",
        "CHF",
      ].includes(currency)
      ? new Intl.NumberFormat(undefined, {
          style: "currency",
          currency,
        }).format(v)
      : new Intl.NumberFormat(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(v)
    : v == null || v === "UNKNOWN"
      ? "—"
      : String(v);
function App() {
  const [docs, setDocs] = useState<DocumentRecord[]>([]),
    [selected, setSelected] = useState<string | null>(null),
    [health, setHealth] = useState("Checking"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [drag, setDrag] = useState(false);
  const refresh = async () => {
    try {
      const [data, h] = await Promise.all([api.list(), api.health()]);
      setDocs(data.items);
      setHealth(h.database === "ok" ? "Connected" : "Degraded");
    } catch (e) {
      setError((e as Error).message);
      setHealth("Unavailable");
    }
  };
  useEffect(() => {
    void refresh();
  }, []);
  const doc = docs.find((d) => d.id === selected) ?? docs[0] ?? null;
  const stats = useMemo(() => {
    const timings = docs
      .map((d) => d.processing_time_ms)
      .filter((x): x is number => x !== null);
    return {
      total: docs.length,
      done: docs.filter(
        (d) => d.status === "completed" && d.extraction_status === "completed",
      ).length,
      failed: docs.filter((d) => d.status === "failed").length,
      avg: timings.length
        ? timings.reduce((a, x) => a + x, 0) / timings.length
        : null,
    };
  }, [docs]);
  async function upload(file?: File) {
    if (!file) return;
    setError("");
    setBusy(true);
    try {
      const created = await api.upload(file);
      setSelected(created.id);
      await refresh();
      const result = await api.process(created.id);
      setDocs((v) => [result, ...v.filter((x) => x.id !== result.id)]);
      setSelected(result.id);
    } catch (e) {
      setError((e as Error).message);
      await refresh();
    } finally {
      setBusy(false);
    }
  }
  async function retry(id: string) {
    setBusy(true);
    setError("");
    try {
      const result = await api.process(id);
      setDocs((current) => [
        result,
        ...current.filter((item) => item.id !== id),
      ]);
      setSelected(id);
    } catch (e) {
      setError((e as Error).message);
      await refresh();
    } finally {
      setBusy(false);
    }
  }
  async function remove(id: string) {
    try {
      await api.remove(id);
      setDocs((v) => v.filter((d) => d.id !== id));
      setSelected(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function exportJson(d: DocumentRecord) {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            document_id: d.id,
            fields: d.extracted_fields,
            validation: d.validation,
            raw_extraction: d.raw_extraction,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${d.original_filename}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }
  const keys = [
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "due_date",
    "currency",
    "subtotal",
    "tax",
    "total",
    "vendor_address",
    "customer_name",
    "tax_id",
  ];
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <FileText size={20} />
          </div>
          <div>
            <b>Papertrail</b>
            <span>DOCUMENT INTELLIGENCE</span>
          </div>
        </div>
        <div className="side-label">WORKSPACE</div>
        <div className="nav active">
          <Activity size={17} />
          Overview
        </div>
        <div className="side-foot">
          <div className="status-dot" />
          <div>
            <b>API {health}</b>
            <span>Local workspace</span>
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <span className="muted">Workspace</span>
            <ChevronRight size={14} />
            <b>Overview</b>
          </div>
          <div className="model-pill">
            <BrainCircuit size={15} /> Donut · CORD pretrained
          </div>
        </header>
        <section className="content">
          <div className="heading">
            <div>
              <p className="eyebrow">DOCUMENT WORKSPACE</p>
              <h1>Invoice intelligence</h1>
              <p className="sub">
                Turn invoice documents into reviewable, structured data.
              </p>
            </div>
            <label className={`upload-btn ${busy ? "disabled" : ""}`}>
              <Upload size={16} />
              {busy ? "Processing…" : "Upload document"}
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.webp"
                disabled={busy}
                onChange={(e) => void upload(e.target.files?.[0])}
              />
            </label>
          </div>
          {error && (
            <div className="error">
              <AlertTriangle size={16} />
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}
          <div className="stats">
            <Stat icon={<FileText />} label="Documents" value={stats.total} />
            <Stat
              icon={<CheckCircle2 />}
              label="Processed"
              value={stats.done}
            />
            <Stat
              icon={<AlertTriangle />}
              label="Failed"
              value={stats.failed}
            />
            <Stat
              icon={<Clock3 />}
              label="Avg. processing"
              value={stats.avg === null ? "—" : `${Math.round(stats.avg)} ms`}
            />
          </div>
          <div className="grid">
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Recent documents</h2>
                  <p>Uploaded and processed invoices</p>
                </div>
                <button
                  className="icon-btn"
                  onClick={() => void refresh()}
                  title="Refresh"
                >
                  <RefreshCw size={16} />
                </button>
              </div>
              <div
                className={`dropzone ${drag ? "drag" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDrag(true);
                }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDrag(false);
                  void upload(e.dataTransfer.files[0]);
                }}
              >
                <Upload size={18} />
                <span>
                  Drop an invoice here or{" "}
                  <label>
                    browse
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.webp"
                      onChange={(e) => void upload(e.target.files?.[0])}
                    />
                  </label>
                </span>
                <small>PDF or image · up to 15 MB</small>
              </div>
              <div className="doc-list">
                {docs.length === 0 ? (
                  <div className="empty">
                    <FileText size={26} />
                    <b>No documents yet</b>
                    <span>Upload a PDF or image to get started.</span>
                  </div>
                ) : (
                  docs.map((d) => (
                    <button
                      className={`doc-row ${doc?.id === d.id ? "selected" : ""}`}
                      key={d.id}
                      onClick={() => setSelected(d.id)}
                    >
                      <div className="file-icon">
                        <FileText size={17} />
                      </div>
                      <div className="doc-name">
                        <b>{d.original_filename}</b>
                        <span>{new Date(d.created_at).toLocaleString()}</span>
                      </div>
                      <Status value={d.status} />
                    </button>
                  ))
                )}
              </div>
            </section>
            <section className="panel result-panel">
              {doc ? (
                <>
                  <div className="panel-head">
                    <div>
                      <p className="eyebrow">EXTRACTION RESULT</p>
                      <h2>{doc.original_filename}</h2>
                      <p>
                        {doc.processing_time_ms
                          ? `${doc.processing_time_ms.toFixed(0)} ms processing · `
                          : ""}
                        {doc.ocr_result?.page_count ?? "—"} page(s)
                      </p>
                    </div>
                    <div className="actions">
                      {doc.status === "failed" && (
                        <button
                          className="icon-btn"
                          title="Retry processing"
                          disabled={busy}
                          onClick={() => void retry(doc.id)}
                        >
                          <RefreshCw size={16} />
                        </button>
                      )}
                      <button
                        className="icon-btn"
                        title="Export JSON"
                        onClick={() => exportJson(doc)}
                      >
                        <Download size={16} />
                      </button>
                      <button
                        className="icon-btn danger-icon"
                        title="Delete"
                        onClick={() => void remove(doc.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                  <div
                    className={`validation ${doc.validation?.status === "passed" ? "pass" : "warn"}`}
                  >
                    {doc.validation?.status === "passed" ? (
                      <CheckCircle2 size={17} />
                    ) : (
                      <AlertTriangle size={17} />
                    )}
                    <div>
                      <b>Validation {doc.validation?.status ?? "pending"}</b>
                      {(doc.validation?.issues ?? []).map((issue) => (
                        <span key={issue}>{issue}</span>
                      ))}
                    </div>
                  </div>
                  <div className="field-grid">
                    {keys.map((key) => {
                      const field = doc.extracted_fields?.[key];
                      if (!field) return null;
                      const val =
                        key === "subtotal" || key === "tax" || key === "total"
                          ? money(
                              field.value,
                              doc.extracted_fields?.currency?.value,
                            )
                          : field.value;
                      return (
                        <div className="field" key={key}>
                          <span>{human(key)}</span>
                          <b>
                            {typeof val === "object" && val !== null
                              ? JSON.stringify(val)
                              : String(val ?? "—")}
                          </b>
                          <div className="confidence">
                            {field.confidence !== null &&
                            field.confidence !== undefined ? (
                              <>
                                <i>
                                  <em
                                    style={{
                                      width: `${Math.round(field.confidence * 100)}%`,
                                    }}
                                  />
                                </i>
                                <span>
                                  {(field.confidence * 100).toFixed(1)}% ·{" "}
                                  {field.source}
                                </span>
                              </>
                            ) : (
                              <span>{field.source ?? "Not identified"}</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {Array.isArray(doc.extracted_fields?.line_items?.value) && (
                    <div className="line-items">
                      <h3>Line items</h3>
                      <table>
                        <thead>
                          <tr>
                            <th>Description</th>
                            <th>Qty</th>
                            <th>Unit price</th>
                            <th>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(
                            doc.extracted_fields.line_items.value as {
                              description?: string;
                              quantity?: number;
                              unit_price?: number;
                              amount?: number;
                            }[]
                          ).map((item, i) => (
                            <tr key={i}>
                              <td>{item.description ?? "—"}</td>
                              <td>{item.quantity ?? "—"}</td>
                              <td>
                                {money(
                                  item.unit_price,
                                  doc.extracted_fields?.currency?.value,
                                )}
                              </td>
                              <td>
                                {money(
                                  item.amount,
                                  doc.extracted_fields?.currency?.value,
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <span className="tiny">
                        Donut sequence confidence:{" "}
                        {doc.extracted_fields.line_items.confidence == null
                          ? "not available"
                          : `${(doc.extracted_fields.line_items.confidence * 100).toFixed(1)}%`}
                      </span>
                    </div>
                  )}
                  <details className="preview">
                    <summary>Original document preview</summary>
                    {doc.content_type === "application/pdf" ? (
                      <iframe
                        title="Original invoice PDF"
                        src={api.fileUrl(doc.id)}
                      />
                    ) : (
                      <img alt="Uploaded invoice" src={api.fileUrl(doc.id)} />
                    )}
                  </details>
                  <details className="ocr">
                    <summary>OCR text and extraction details</summary>
                    <pre>
                      {doc.ocr_result?.text ?? "No OCR text available."}
                    </pre>
                    <p className="tiny">
                      OCR engine confidence:{" "}
                      {doc.ocr_result?.mean_confidence == null
                        ? "—"
                        : `${(doc.ocr_result.mean_confidence * 100).toFixed(1)}%`}
                      . Donut sequence confidence is a whole generated-sequence
                      score, not a field-specific probability; OCR-only
                      candidates have no extraction confidence.
                    </p>
                    <pre>{JSON.stringify(doc.raw_extraction, null, 2)}</pre>
                  </details>
                </>
              ) : (
                <div className="empty result-empty">
                  <FileText size={30} />
                  <b>Select a document</b>
                  <span>
                    Choose a recent upload to review extracted fields.
                  </span>
                </div>
              )}
            </section>
          </div>
          <footer>
            Pretrained model outputs require human review. Validation checks
            consistency; it does not certify invoice correctness.
          </footer>
        </section>
      </main>
    </div>
  );
}
function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}) {
  return (
    <div className="stat">
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <b>{value}</b>
      </div>
    </div>
  );
}
function Status({ value }: { value: string }) {
  return (
    <span
      className={`badge ${value === "completed" ? "success" : value === "failed" ? "failed" : value.includes("warning") || value === "processing" ? "working" : "neutral"}`}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}
export default App;
