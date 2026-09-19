import { useState } from "react";
import { api } from "../../services/api";

export default function PatchHistoryPanel({
  workspaceId,
  dashboardId,
  history,
  currentVersion,
  onRolledBack,
}) {
  const [rolling, setRolling] = useState(null);
  const [error, setError] = useState(null);

  const handleRollback = async (targetVersion) => {
    if (!confirm(`Rollback ke versi ${targetVersion}? Versi saat ini (v${currentVersion}) akan menjadi parent.`)) return;
    setError(null);
    setRolling(targetVersion);
    try {
      const newState = await api.rollbackDashboard(workspaceId, dashboardId, {
        target_version: targetVersion,
        base_version: currentVersion,
      });
      if (onRolledBack) onRolledBack(newState);
    } catch (err) {
      setError(err.message);
    } finally {
      setRolling(null);
    }
  };

  return (
    <div style={{ padding: 12 }}>
      <div style={{ marginBottom: 10 }}>
        <strong style={{ fontSize: 13 }}>Version History</strong>
        <span style={{ fontSize: 11, color: "var(--ios-text-secondary)", marginLeft: 8 }}>
          ({history?.length || 0} versions)
        </span>
      </div>

      {error && (
        <div style={{ color: "#f87171", fontSize: 11, marginBottom: 8 }}>{error}</div>
      )}

      {(!history || history.length === 0) && (
        <div style={{ fontSize: 11, color: "var(--ios-text-tertiary)" }}>No versions yet.</div>
      )}

      {history?.map((v) => {
        const isCurrent = v.version === currentVersion;
        return (
          <div
            key={v.id}
            style={{
              padding: 8,
              marginBottom: 6,
              borderRadius: 6,
              border: isCurrent ? "1px solid #3b82f6" : "1px solid var(--ios-separator)",
              background: isCurrent ? "rgba(59,130,246,0.1)" : "transparent",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: 12,
            }}
          >
            <div>
              <div style={{ fontWeight: 600 }}>
                v{v.version}
                {isCurrent && <span style={{ marginLeft: 6, fontSize: 10, color: "#3b82f6" }}>current</span>}
              </div>
              <div style={{ fontSize: 10, color: "var(--ios-text-tertiary)", marginTop: 2 }}>
                {v.parent_version ? `from v${v.parent_version}` : "initial"}
              </div>
            </div>
            {!isCurrent && (
              <button
                onClick={() => handleRollback(v.version)}
                disabled={rolling === v.version}
                style={{
                  padding: "4px 10px",
                  borderRadius: 4,
                  border: "none",
                  background: "#6b7280",
                  color: "white",
                  fontSize: 10,
                  cursor: "pointer",
                }}
              >
                {rolling === v.version ? "..." : "Rollback"}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}