import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

export default function SchemaBuilderPage() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);

  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState("");
  const [ddl, setDdl] = useState("");
  const [columnsResolved, setColumnsResolved] = useState([]);
  const [tableName, setTableName] = useState("");
  const [existingSchema, setExistingSchema] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [rolling, setRolling] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      if (!activeWorkspace?.id) return;
      setLoading(true);
      try {
        const list = await api.listDatasets(activeWorkspace.id);
        setDatasets(list || []);
        const candidate = list.find((d) => !d.schema_applied) || list[0] || null;
        if (candidate) setDatasetId(candidate.id);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [activeWorkspace?.id]);

  useEffect(() => {
    (async () => {
      if (!datasetId) {
        setExistingSchema(null);
        return;
      }
      try {
        const schema = await api.getSchemaForDataset(activeWorkspace.id, datasetId);
        setExistingSchema(schema);
        if (schema) {
          setDdl(schema.ddl);
          setTableName(schema.table_name);
          setColumnsResolved(schema.columns_json || []);
        } else {
          setDdl("");
          setTableName("");
          setColumnsResolved([]);
        }
      } catch {
        setExistingSchema(null);
      }
    })();
  }, [datasetId, activeWorkspace?.id]);

  const handleGenerate = async () => {
    setError(null);
    setStatus(null);
    setGenerating(true);
    try {
      const res = await api.generateDDL(activeWorkspace.id, { dataset_id: datasetId });
      setDdl(res.ddl);
      setColumnsResolved(res.columns_resolved);
      setTableName(res.table_name);
      setStatus("DDL generated. Review, edit if needed, then Apply.");
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleApply = async () => {
    setError(null);
    setStatus(null);
    setApplying(true);
    try {
      const res = await api.applySchema(activeWorkspace.id, {
        dataset_id: datasetId,
        ddl,
        columns_resolved: columnsResolved,
        table_name: tableName,
        drop_if_exists: true,
      });
      setStatus(`Applied: ${res.table_name} — ${res.rows_inserted} rows inserted.`);
      const schema = await api.getSchemaForDataset(activeWorkspace.id, datasetId);
      setExistingSchema(schema);
    } catch (err) {
      setError(err.message);
    } finally {
      setApplying(false);
    }
  };

  const handleRollback = async () => {
    if (!confirm(`Drop table "${tableName}"? This removes all data.`)) return;
    setError(null);
    setStatus(null);
    setRolling(true);
    try {
      await api.rollbackSchema(activeWorkspace.id, {
        dataset_id: datasetId,
        table_name: tableName,
      });
      setStatus(`Rolled back: ${tableName}`);
      setDdl("");
      setExistingSchema(null);
      await api.listDatasets(activeWorkspace.id).then(setDatasets);
    } catch (err) {
      setError(err.message);
    } finally {
      setRolling(false);
    }
  };

  if (!activeWorkspace) return <div style={{ padding: 32 }}>No workspace selected</div>;

  return (
    <div style={{ minHeight: "100vh", padding: "32px 24px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <header style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>Schema Builder</h1>
          <p style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>
            Auto-generate DDL from a dataset, review with syntax highlighting, apply to the connector.
          </p>
        </header>

        <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 16, background: "var(--ios-surface)", marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, marginBottom: 6 }}>Dataset</label>
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            disabled={loading}
            style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid var(--ios-separator)", background: "transparent", color: "inherit", fontSize: 13 }}
          >
            {loading && <option>Loading datasets...</option>}
            {!loading && datasets.length === 0 && <option value="">No datasets — upload one first</option>}
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.row_count} rows{d.schema_applied ? " — applied" : ""})
              </option>
            ))}
          </select>

          {existingSchema && (
            <div style={{ marginTop: 10, fontSize: 12, color: "#10b981" }}>
              Existing schema: <strong>{existingSchema.table_name}</strong> ({existingSchema.status})
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <button onClick={handleGenerate} disabled={generating || !datasetId} style={btn("#6b7280")}>
            {generating ? "Generating..." : "Generate DDL"}
          </button>
          <button onClick={handleApply} disabled={applying || !ddl} style={btn("#10b981")}>
            {applying ? "Applying..." : "Apply Schema"}
          </button>
          <button onClick={handleRollback} disabled={rolling || !existingSchema} style={btn("#ef4444")}>
            {rolling ? "Rolling back..." : "Rollback"}
          </button>
        </div>

        {status && (
          <div style={{ color: "#10b981", background: "rgba(16,185,129,0.08)", padding: "10px 14px", borderRadius: 8, marginBottom: 12, fontSize: 13 }}>
            {status}
          </div>
        )}
        {error && (
          <div style={{ color: "#f87171", background: "rgba(248,113,113,0.08)", padding: "10px 14px", borderRadius: 8, marginBottom: 12, fontSize: 13 }}>
            {error}
          </div>
        )}

        {ddl && (
          <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, overflow: "hidden" }}>
            <div style={{ padding: "8px 14px", background: "rgba(255,255,255,0.03)", fontSize: 12, color: "var(--ios-text-secondary)", borderBottom: "1px solid var(--ios-separator)" }}>
              {tableName} — {columnsResolved.length} columns
            </div>
            <Editor
              height="400px"
              defaultLanguage="sql"
              value={ddl}
              onChange={(v) => setDdl(v || "")}
              theme="vs-dark"
              options={{ minimap: { enabled: false }, fontSize: 13, lineNumbers: "on" }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function btn(bg) {
  return {
    padding: "8px 16px",
    borderRadius: 6,
    border: "none",
    background: bg,
    color: "white",
    fontSize: 13,
    cursor: "pointer",
  };
}