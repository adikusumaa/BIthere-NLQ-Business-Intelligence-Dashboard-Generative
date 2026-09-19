export default function PropertyPanel({ workspaceId, dashboardId, state, selectedCardId, sessionId, onApplied }) {
  return <div style={{ padding: 16 }}>PropertyPanel — selected: {selectedCardId || "none"}</div>;
}