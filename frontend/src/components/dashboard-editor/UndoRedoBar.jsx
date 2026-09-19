export default function UndoRedoBar({ workspaceId, dashboardId, sessionId, onChanged }) {
  return (
    <div style={{ padding: "6px 16px", borderBottom: "1px solid var(--ios-separator)", background: "var(--ios-surface)", fontSize: 12, color: "var(--ios-text-secondary)" }}>
      Editor session: {sessionId} (undo/redo WIP)
    </div>
  );
}