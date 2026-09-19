import { useRef, useState } from "react";
import { api } from "../../../services/api";
import { useWorkspaceStore } from "../../../store/workspaceStore";
import { useWizardStore } from "../../../store/wizardStore";

export default function Step4DatasetUpload({ onNext, onBack }) {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const saveStep = useWizardStore((s) => s.saveStep);

  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [name, setName] = useState("");

  const handleFile = async (file) => {
    setError(null);
    setResult(null);
    setUploading(true);
    try {
      const res = await api.uploadDataset(activeWorkspace.id, file, {
        name: name || file.name,
        target: "duckdb",
      });
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleContinue = async () => {
    if (!result) {
      setError("Upload a file first");
      return;
    }
    await saveStep(activeWorkspace.id, 4, { dataset_id: result.dataset_id });
    onNext();
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>Step 4 — Dataset Upload</h2>
      <p style={{ color: "var(--ios-text-secondary)", marginBottom: 20, fontSize: 14 }}>
        Upload CSV, Excel, or Parquet. Max 500 MB.
      </p>

      <label style={labelStyle}>Dataset name (optional)</label>
      <input value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          marginTop: 16,
          border: "2px dashed #374151",
          borderRadius: 12,
          padding: 40,
          textAlign: "center",
          cursor: "pointer",
          color: "var(--ios-text-secondary)",
        }}
      >
        {uploading ? "Uploading..." : "Drag & drop file here, or click to choose"}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls,.parquet"
        style={{ display: "none" }}
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />

      {error && <div style={{ color: "#f87171", marginTop: 12, fontSize: 13 }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 14, marginBottom: 8 }}>
            <strong>{result.name}</strong> — {result.row_count} rows × {result.column_count} cols
          </div>
          <div style={{ overflow: "auto", maxHeight: 260, border: "1px solid #374151", borderRadius: 8 }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead style={{ background: "rgba(255,255,255,0.05)" }}>
                <tr>
                  {result.preview.columns.map((c) => (
                    <th key={c} style={{ padding: 6, textAlign: "left", borderBottom: "1px solid #374151" }}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.preview.rows.slice(0, 20).map((row, i) => (
                  <tr key={i}>
                    {result.preview.columns.map((c) => (
                      <td key={c} style={{ padding: 6, borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        {row[c] == null ? "—" : String(row[c]).slice(0, 30)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: "var(--ios-text-secondary)" }}>
            Showing {Math.min(20, result.preview.rows.length)} of {result.row_count} rows
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <button onClick={onBack} style={btnStyle("#6b7280")}>Back</button>
        <button onClick={handleContinue} disabled={!result} style={btnStyle("#3b82f6")}>Save & Continue</button>
      </div>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 13, marginBottom: 6, marginTop: 12 };
const inputStyle = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: 6,
  border: "1px solid #374151",
  background: "transparent",
  color: "inherit",
  fontSize: 13,
};
function btnStyle(bg) {
  return { padding: "8px 16px", borderRadius: 6, border: "none", background: bg, color: "white", fontSize: 13, cursor: "pointer" };
}