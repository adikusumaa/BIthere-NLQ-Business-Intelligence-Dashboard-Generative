import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import ConfirmDialog from "../../components/ConfirmDialog";
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
  const [confirmRollback, setConfirmRollback] = useState(false);

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

  const handleRollback = () => {
    if (!tableName) return;
    setConfirmRollback(true);
  };

  const confirmRollbackNow = async () => {
    setConfirmRollback(false);
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

  if (!activeWorkspace) {
    return <div style={{ padding: 32 }}>No workspace selected</div>;
  }

  return (
    <div style={{ minHeight: "100vh", padding: "32px 24px 60px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <header style={{ marginBottom: 28 }}>
          <h1
            style={{
              fontSize: 34,
              fontWeight: 700,
              letterSpacing: "-0.03em",
              color: "var(--ios-text)",
              marginBottom: 4,
            }}
          >
            Schema Builder
          </h1>
          <p style={{ fontSize: 15, color: "var(--ios-text-secondary)" }}>
            Auto-generate DDL from a dataset, review, then apply to the connector.
          </p>
        </header>

        <div
          style={{
            background: "var(--ios-surface)",
            borderRadius: "var(--radius-md)",
            padding: "16px 20px",
            marginBottom: 16,
            border: "1px solid var(--ios-separator)",
            boxShadow: "var(--shadow-xs)",
          }}
        >
          <label
            style={{
              display: "block",
              fontSize: 13,
              fontWeight: 600,
              color: "var(--ios-text-secondary)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              marginBottom: 8,
            }}
          >
            Dataset
          </label>
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            disabled={loading}
            className="ios-input"
            style={{ width: "100%" }}
          >
            {loading && <option>Loading datasets...</option>}
            {!loading && datasets.length === 0 && (
              <option value="">No datasets — upload one first</option>
            )}
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.row_count} rows{d.schema_applied ? " — applied" : ""})
              </option>
            ))}
          </select>

          {existingSchema && (
            <div
              style={{
                marginTop: 12,
                fontSize: 13,
                color: "var(--ios-green)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span>✓</span>
              <span>
                Existing schema: <strong>{existingSchema.table_name}</strong> ({existingSchema.status})
              </span>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          <button
            onClick={handleGenerate}
            disabled={generating || !datasetId}
            className="ios-btn ios-btn-pill"
            style={{ padding: "10px 20px", fontSize: 15, fontWeight: 600 }}
          >
            {generating ? "Generating..." : "Generate DDL"}
          </button>
          <button
            onClick={handleApply}
            disabled={applying || !ddl}
            className="ios-btn ios-btn-pill"
            style={{
              padding: "10px 20px",
              fontSize: 15,
              fontWeight: 600,
              background: "var(--ios-green)",
              color: "#FFFFFF",
            }}
          >
            {applying ? "Applying..." : "Apply Schema"}
          </button>
          <button
            onClick={handleRollback}
            disabled={rolling || !existingSchema}
            className="ios-btn ios-btn-pill"
            style={{
              padding: "10px 20px",
              fontSize: 15,
              fontWeight: 600,
              background: "var(--ios-red)",
              color: "#FFFFFF",
            }}
          >
            {rolling ? "Rolling back..." : "Rollback"}
          </button>
        </div>

        {status && (
          <div
            style={{
              background: "rgba(52, 199, 89, 0.10)",
              color: "var(--ios-green)",
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              marginBottom: 16,
              fontSize: 14,
              border: "1px solid rgba(52, 199, 89, 0.24)",
            }}
          >
            {status}
          </div>
        )}
        {error && (
          <div
            style={{
              background: "rgba(255, 59, 48, 0.10)",
              color: "var(--ios-red)",
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              marginBottom: 16,
              fontSize: 14,
              border: "1px solid rgba(255, 59, 48, 0.24)",
            }}
          >
            {error}
          </div>
        )}

        {ddl && (
          <div
            style={{
              background: "var(--ios-surface)",
              borderRadius: "var(--radius-md)",
              overflow: "hidden",
              border: "1px solid var(--ios-separator)",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div
              style={{
                padding: "10px 18px",
                background: "var(--ios-surface-2)",
                fontSize: 13,
                fontWeight: 600,
                color: "var(--ios-text-secondary)",
                borderBottom: "1px solid var(--ios-separator)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>{tableName}</span>
              <span style={{ fontWeight: 400, color: "var(--ios-text-tertiary)" }}>
                {columnsResolved.length} columns
              </span>
            </div>
            <Editor
              height="420px"
              defaultLanguage="sql"
              value={ddl}
              onChange={(v) => setDdl(v || "")}
              theme="vs"
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: "on",
                fontFamily: "SF Mono, Monaco, Menlo, monospace",
                scrollBeyondLastLine: false,
                renderLineHighlight: "none",
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmRollback}
        title="Drop table?"
        message={`This will permanently drop "${tableName}" and remove all its data. This action cannot be undone.`}
        confirmLabel="Drop Table"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={confirmRollbackNow}
        onCancel={() => setConfirmRollback(false)}
      />
    </div>
  );
}