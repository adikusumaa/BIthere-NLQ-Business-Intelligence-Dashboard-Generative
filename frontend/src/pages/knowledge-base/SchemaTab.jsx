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

  if (loading) return <div style={{ color: "var(--ios-text-secondary)" }}>Loading schema...</div>;
  if (error) return <div style={{ color: "#f87171", fontSize: 13 }}>{error}</div>;
  if (!schema || Object.keys(schema).length === 0) {
    return <div style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>No tables found. Upload a dataset and apply schema first.</div>;
  }

  return (
    <div>
      <div style={{ fontSize: 12, color: "var(--ios-text-secondary)", marginBottom: 12 }}>
        Dialect: <strong>{dialect}</strong> · {Object.keys(schema).length} table(s)
      </div>
      {Object.entries(schema).map(([table, columns]) => (
        <div
          key={table}
          style={{
            border: "1px solid var(--ios-separator)",
            borderRadius: 10,
            padding: 16,
            marginBottom: 10,
            background: "var(--ios-surface)",
          }}
        >
          <strong style={{ fontSize: 14 }}>{table}</strong>
          <div style={{ marginTop: 10, fontSize: 12 }}>
            {columns.map((c) => (
              <div key={c.column} style={{ padding: "3px 0", color: "var(--ios-text-secondary)" }}>
                <span style={{ color: "inherit", fontFamily: "monospace" }}>{c.column}</span>
                <span style={{ marginLeft: 8, color: "var(--ios-text-tertiary)" }}>{c.type}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}