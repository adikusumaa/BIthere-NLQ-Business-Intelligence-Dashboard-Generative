import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function DiffViewer({ workspaceId, dashboardId, v1, v2, onClose }) {
  const [diff, setDiff] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.diffDashboard(workspaceId, dashboardId, v1, v2);
        setDiff(res);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [workspaceId, dashboardId, v1, v2]);

  if (loading) return <div style={{ padding: 16, fontSize: 12 }}>Loading diff...</div>;
  if (error) return <div style={{ padding: 16, fontSize: 12, color: "#f87171" }}>{error}</div>;
  if (!diff) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--ios-surface)",
          borderRadius: 12,
          padding: 24,
          maxWidth: 640,
          width: "90%",
          maxHeight: "80vh",
          overflow: "auto",
          border: "1px solid var(--ios-separator)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 16 }}>Diff v{diff.from_version} → v{diff.to_version}</h3>
          </div>
          <button onClick={onClose} style={closeBtn}>×</button>
        </div>

        <Section title="Added cards" items={diff.added} color="#10b981" emptyText="No cards added" />
        <Section title="Removed cards" items={diff.removed} color="#ef4444" emptyText="No cards removed" />
        <Section title="Moved cards" items={diff.moved} color="#f59e0b" emptyText="No cards moved" />

        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
            Modified fields ({diff.modified.length})
          </div>
          {diff.modified.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--ios-text-tertiary)" }}>No field changes</div>
          ) : (
            diff.modified.map((m, i) => (
              <div
                key={i}
                style={{
                  fontSize: 12,
                  padding: "4px 8px",
                  background: "rgba(59,130,246,0.08)",
                  borderRadius: 4,
                  marginBottom: 4,
                }}
              >
                <span style={{ fontFamily: "monospace" }}>{m.card_id}</span>
                {" → "}
                <strong>{m.field}</strong>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, items, color, emptyText }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>
        {title} ({items.length})
      </div>
      {items.length === 0 ? (
        <div style={{ fontSize: 12, color: "var(--ios-text-tertiary)" }}>{emptyText}</div>
      ) : (
        items.map((id) => (
          <div
            key={id}
            style={{
              fontSize: 12,
              padding: "4px 8px",
              background: `${color}20`,
              borderLeft: `3px solid ${color}`,
              borderRadius: 4,
              marginBottom: 4,
              fontFamily: "monospace",
            }}
          >
            {id}
          </div>
        ))
      )}
    </div>
  );
}

const closeBtn = {
  width: 28,
  height: 28,
  borderRadius: 6,
  border: "none",
  background: "transparent",
  color: "inherit",
  fontSize: 20,
  cursor: "pointer",
};