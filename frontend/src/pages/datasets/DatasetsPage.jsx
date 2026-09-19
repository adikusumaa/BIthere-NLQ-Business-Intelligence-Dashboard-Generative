import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

export default function DatasetsPage() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [uploadName, setUploadName] = useState("");
  const inputRef = useRef(null);

  const load = async () => {
    if (!activeWorkspace?.id) return;
    setLoading(true);
    setError(null);
    try {
      const list = await api.listDatasets(activeWorkspace.id);
      setDatasets(list);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [activeWorkspace?.id]);

  const handleFile = async (file) => {
    setError(null);
    setUploading(true);
    try {
      await api.uploadDataset(activeWorkspace.id, file, {
        name: uploadName || file.name,
        target: "duckdb",
      });
      setUploadName("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete dataset "${name}"?`)) return;
    try {
      await api.deleteDataset(activeWorkspace.id, id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handlePreview = async (id) => {
    setPreview({ id, loading: true });
    try {
      const data = await api.previewDataset(activeWorkspace.id, id, 100);
      setPreview({ id, data });
    } catch (err) {
      setError(err.message);
      setPreview(null);
    }
  };

  if (!activeWorkspace) {
    return <div style={{ padding: 32 }}>No workspace selected</div>;
  }

  return (
    <div style={{ minHeight: "100vh", padding: "32px 24px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <header style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>Datasets</h1>
          <p style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>
            Upload CSV, Excel, or Parquet. Max 500 MB per file.
          </p>
        </header>

        {error && (
          <div style={{ color: "#f87171", background: "rgba(248,113,113,0.08)", padding: "10px 14px", borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 16, background: "var(--ios-surface)", marginBottom: 24 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <input
              type="text"
              placeholder="Dataset name (optional)"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              style={{ flex: 1, padding: "8px 12px", borderRadius: 6, border: "1px solid var(--ios-separator)", background: "transparent", color: "inherit", fontSize: 13 }}
            />
          </div>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) handleFile(f); }}
            onClick={() => inputRef.current?.click()}
            style={{ border: "2px dashed var(--ios-separator)", borderRadius: 10, padding: 32, textAlign: "center", cursor: "pointer", color: "var(--ios-text-secondary)", fontSize: 14 }}
          >
            {uploading ? "Uploading..." : "Drag & drop file here, or click to choose"}
          </div>
          <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls,.parquet" style={{ display: "none" }}
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
        </div>

        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Your datasets</h2>

        {loading && <div style={{ color: "var(--ios-text-secondary)" }}>Loading...</div>}
        {!loading && datasets.length === 0 && (
          <div style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>No datasets yet.</div>
        )}

        {datasets.map((ds) => (
          <div key={ds.id} style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 16, marginBottom: 10, background: "var(--ios-surface)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <div>
                <strong style={{ fontSize: 14 }}>{ds.name}</strong>
                <div style={{ fontSize: 12, color: "var(--ios-text-secondary)", marginTop: 4 }}>
                  {ds.source_type.toUpperCase()} · {ds.row_count ?? "?"} rows × {ds.column_count ?? "?"} cols
                  {ds.schema_applied && <span style={{ color: "#10b981", marginLeft: 8 }}>✓ applied</span>}
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => handlePreview(ds.id)} style={btn("#6b7280")}>Preview</button>
                <button onClick={() => handleDelete(ds.id, ds.name)} style={btn("#ef4444")}>Delete</button>
              </div>
            </div>
          </div>
        ))}

        {preview && (
          <div style={{ marginTop: 20, border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 16, background: "var(--ios-surface)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
              <strong style={{ fontSize: 14 }}>Preview</strong>
              <button onClick={() => setPreview(null)} style={btn("#6b7280")}>Close</button>
            </div>
            {preview.loading ? (
              <div style={{ color: "var(--ios-text-secondary)" }}>Loading preview...</div>
            ) : (
              <div style={{ overflow: "auto", maxHeight: 400 }}>
                <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                  <thead style={{ background: "rgba(255,255,255,0.05)" }}>
                    <tr>
                      {preview.data.columns.map((c) => (
                        <th key={c} style={{ padding: 6, textAlign: "left", borderBottom: "1px solid var(--ios-separator)" }}>{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.data.rows.slice(0, 50).map((row, i) => (
                      <tr key={i}>
                        {preview.data.columns.map((c) => (
                          <td key={c} style={{ padding: 6, borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                            {row[c] == null ? "—" : String(row[c]).slice(0, 30)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function btn(bg) {
  return {
    padding: "7px 14px",
    borderRadius: 6,
    border: "none",
    background: bg,
    color: "white",
    fontSize: 13,
    cursor: "pointer",
  };
}