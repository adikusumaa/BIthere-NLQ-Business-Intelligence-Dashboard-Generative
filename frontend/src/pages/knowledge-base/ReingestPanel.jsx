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
      <div
        style={{
          background: "var(--ios-surface)",
          borderRadius: "var(--radius-md)",
          padding: "22px 24px",
          border: "1px solid var(--ios-separator)",
          boxShadow: "var(--shadow-xs)",
        }}
      >
        <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 8, color: "var(--ios-text)" }}>
          Re-ingest to Pinecone
        </div>
        <p
          style={{
            color: "var(--ios-text-secondary)",
            fontSize: 14,
            lineHeight: 1.6,
            marginBottom: 16,
          }}
        >
          Rebuilds the vector namespace from your current schema and glossary.
          Run this after uploading new data, adding terms, or applying schema.
        </p>

        <button
          onClick={handleReingest}
          disabled={running}
          className="ios-btn ios-btn-pill"
          style={{
            padding: "11px 24px",
            fontSize: 15,
            fontWeight: 600,
            background: "var(--ios-green)",
            color: "#FFFFFF",
            cursor: running ? "wait" : "pointer",
          }}
        >
          {running ? "Re-ingesting..." : "Re-ingest now"}
        </button>

        {result && (
          <div
            style={{
              marginTop: 18,
              padding: "16px 18px",
              background: "rgba(52, 199, 89, 0.10)",
              borderRadius: "var(--radius-md)",
              fontSize: 14,
              border: "1px solid rgba(52, 199, 89, 0.24)",
            }}
          >
            <div style={{ color: "var(--ios-green)", fontWeight: 700, marginBottom: 8 }}>
              Ingestion complete
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ color: "var(--ios-text-secondary)" }}>Schema vectors</span>
              <strong style={{ color: "var(--ios-text)" }}>{result.schema?.vectors ?? 0}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ color: "var(--ios-text-secondary)" }}>Glossary vectors</span>
              <strong style={{ color: "var(--ios-text)" }}>{result.glossary?.vectors ?? 0}</strong>
            </div>
            <div
              style={{
                fontSize: 12,
                marginTop: 10,
                color: "var(--ios-text-tertiary)",
                fontFamily: "SF Mono, Monaco, Menlo, monospace",
                wordBreak: "break-all",
              }}
            >
              {result.namespace}
            </div>
          </div>
        )}

        {error && (
          <div
            style={{
              marginTop: 16,
              padding: "12px 16px",
              background: "rgba(255, 59, 48, 0.10)",
              borderRadius: "var(--radius-md)",
              color: "var(--ios-red)",
              fontSize: 14,
              border: "1px solid rgba(255, 59, 48, 0.24)",
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  );
}