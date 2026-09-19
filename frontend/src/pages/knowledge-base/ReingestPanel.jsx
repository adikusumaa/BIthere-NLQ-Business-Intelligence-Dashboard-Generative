import { useState } from "react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

export default function ReingestPanel() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleReingest = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.reingest(activeWorkspace.id);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 20, background: "var(--ios-surface)" }}>
        <strong style={{ fontSize: 14 }}>Re-ingest to Pinecone</strong>
        <p style={{ color: "var(--ios-text-secondary)", fontSize: 13, marginTop: 8 }}>
          Rebuilds the vector namespace from your current schema and glossary.
          Run this after uploading new data, adding terms, or applying schema.
        </p>
        <button
          onClick={handleReingest}
          disabled={running}
          style={{
            marginTop: 12,
            padding: "10px 18px",
            borderRadius: 8,
            border: "none",
            background: "#10b981",
            color: "white",
            fontSize: 14,
            cursor: running ? "wait" : "pointer",
          }}
        >
          {running ? "Re-ingesting..." : "Re-ingest now"}
        </button>

        {result && (
          <div style={{ marginTop: 16, padding: 14, background: "rgba(16,185,129,0.08)", borderRadius: 8, fontSize: 13 }}>
            <div style={{ color: "#10b981", marginBottom: 6 }}>
              <strong>Ingestion complete</strong>
            </div>
            <div>Schema vectors: <strong>{result.schema?.vectors ?? 0}</strong></div>
            <div>Glossary vectors: <strong>{result.glossary?.vectors ?? 0}</strong></div>
            <div style={{ fontSize: 11, marginTop: 6, color: "var(--ios-text-tertiary)" }}>
              Namespace: {result.namespace}
            </div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 16, padding: 12, background: "rgba(248,113,113,0.08)", borderRadius: 8, color: "#f87171", fontSize: 13 }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}