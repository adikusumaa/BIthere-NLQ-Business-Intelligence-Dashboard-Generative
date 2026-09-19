import { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function UndoRedoBar({ workspaceId, dashboardId, sessionId, onChanged }) {
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);

  const doUndo = async () => {
    setBusy("undo");
    setError(null);
    try {
      const state = await api.undoDashboard(workspaceId, dashboardId, sessionId);
      if (onChanged) onChanged(state);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  const doRedo = async () => {
    setBusy("redo");
    setError(null);
    try {
      const state = await api.redoDashboard(workspaceId, dashboardId, sessionId);
      if (onChanged) onChanged(state);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        doUndo();
      } else if (
        ((e.ctrlKey || e.metaKey) && e.key === "y") ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "Z")
      ) {
        e.preventDefault();
        doRedo();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [workspaceId, dashboardId, sessionId]);

  return (
    <div
      style={{
        padding: "6px 16px",
        borderBottom: "1px solid var(--ios-separator)",
        background: "var(--ios-surface)",
        display: "flex",
        gap: 8,
        alignItems: "center",
        fontSize: 12,
      }}
    >
      <button onClick={doUndo} disabled={busy === "undo"} style={miniBtn}>
        {busy === "undo" ? "..." : "↶ Undo"}
      </button>
      <button onClick={doRedo} disabled={busy === "redo"} style={miniBtn}>
        {busy === "redo" ? "..." : "↷ Redo"}
      </button>
      <span style={{ color: "var(--ios-text-tertiary)", fontSize: 11 }}>
        Ctrl+Z / Ctrl+Y
      </span>
      {error && <span style={{ color: "#f87171", fontSize: 11 }}>{error}</span>}
      <span style={{ marginLeft: "auto", color: "var(--ios-text-tertiary)", fontSize: 10 }}>
        session: {sessionId}
      </span>
    </div>
  );
}

const miniBtn = {
  padding: "4px 10px",
  borderRadius: 4,
  border: "1px solid var(--ios-separator)",
  background: "transparent",
  color: "inherit",
  fontSize: 11,
  cursor: "pointer",
};