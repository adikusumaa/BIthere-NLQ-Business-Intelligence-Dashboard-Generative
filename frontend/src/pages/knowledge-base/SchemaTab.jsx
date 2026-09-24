import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

export default function SchemaTab() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const [schema, setSchema] = useState(null);
  const [dialect, setDialect] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getWorkspaceSchema(activeWorkspace.id);
        setSchema(res.schema);
        setDialect(res.dialect);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [activeWorkspace.id]);

  if (loading) {
    return <div style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>Loading schema...</div>;
  }
  if (error) {
    return (
      <div
        style={{
          color: "var(--ios-red)",
          background: "rgba(255, 59, 48, 0.10)",
          padding: "12px 16px",
          borderRadius: "var(--radius-md)",
          fontSize: 14,
          border: "1px solid rgba(255, 59, 48, 0.24)",
        }}
      >
        {error}
      </div>
    );
  }
  if (!schema || Object.keys(schema).length === 0) {
    return (
      <div style={{ color: "var(--ios-text-secondary)", fontSize: 15 }}>
        No tables found. Upload a dataset and apply schema first.
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          fontSize: 13,
          color: "var(--ios-text-secondary)",
          marginBottom: 14,
          padding: "10px 16px",
          background: "var(--ios-surface)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--ios-separator)",
        }}
      >
        Dialect <strong style={{ color: "var(--ios-text)" }}>{dialect}</strong>
        <span style={{ margin: "0 8px", color: "var(--ios-text-tertiary)" }}>·</span>
        <strong style={{ color: "var(--ios-text)" }}>{Object.keys(schema).length}</strong> table(s)
      </div>

      {Object.entries(schema).map(([table, columns]) => (
        <div
          key={table}
          style={{
            background: "var(--ios-surface)",
            borderRadius: "var(--radius-md)",
            padding: "16px 20px",
            marginBottom: 12,
            border: "1px solid var(--ios-separator)",
            boxShadow: "var(--shadow-xs)",
          }}
        >
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: "var(--ios-text)",
              marginBottom: 12,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>{table}</span>
            <span
              style={{
                fontSize: 12,
                fontWeight: 400,
                color: "var(--ios-text-tertiary)",
              }}
            >
              {columns.length} cols
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {columns.map((c) => (
              <div
                key={c.column}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 14,
                  padding: "4px 0",
                }}
              >
                <span
                  style={{
                    fontFamily: "SF Mono, Monaco, Menlo, monospace",
                    color: "var(--ios-text)",
                  }}
                >
                  {c.column}
                </span>
                <span style={{ color: "var(--ios-text-secondary)", fontSize: 13 }}>
                  {c.type}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}