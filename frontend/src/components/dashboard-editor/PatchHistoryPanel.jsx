export default function PatchHistoryPanel({ workspaceId, dashboardId, history, currentVersion, onRolledBack }) {
  return <div style={{ padding: 16 }}>PatchHistory — {history?.length || 0} versions</div>;
}