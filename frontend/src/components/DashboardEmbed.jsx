import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useWorkspaceStore } from "../store/workspaceStore";

const PANEL_WIDTH = 980;
const RENDER_WIDTH = 1300;
const SCALE = PANEL_WIDTH / RENDER_WIDTH;

export default function DashboardEmbed({ url,metabaseId, onClose }) {
  const navigate = useNavigate();
  const workspaceId = useWorkspaceStore((s) => s.activeWorkspace?.id);
  const [importing, setImporting] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState(null);

  const handleEdit = async () => {
    if (!metabaseId) {
      setError("Dashboard ID not available. Regenerate the dashboard first.");
      return;
    }
    if (!workspaceId) {
      setError("No active workspace.");
      return;
    }
    setError(null);
    setImporting(true);
    try {
      const res = await api.importDashboard(workspaceId, metabaseId);
      navigate(`/dashboard/${res.dashboard_id}/edit`);
    } catch (err) {
      setError(err.message);
    } finally {
      setImporting(false);
    }
  };

  const containerStyle = expanded
    ? {
        position: "fixed",
        inset: "16px 16px 16px 16px",
        zIndex: 200,
        display: "flex",
        flexDirection: "column",
        background: "var(--ios-bg)",
        border: "1px solid var(--ios-separator)",
        borderRadius: 12,
        boxShadow: "0 8px 40px rgba(0,0,0,0.2)",
      }
    : {
        width: PANEL_WIDTH,
        minWidth: 400,
        maxWidth: 900,
        display: "flex",
        flexDirection: "column",
        background: "var(--ios-bg)",
        borderLeft: "1px solid var(--ios-separator)",
      };

  return (
    <>
      {expanded && (
        <div
          onClick={() => setExpanded(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            zIndex: 199,
          }}
        />
      )}

      <div style={containerStyle}>
        <div
          style={{
            display: "flex",
            gap: 6,
            alignItems: "center",
            padding: "8px 12px",
            borderBottom: "1px solid var(--ios-separator)",
            background: "var(--ios-surface)",
            borderTopLeftRadius: expanded ? 12 : 0,
            borderTopRightRadius: expanded ? 12 : 0,
          }}
        >
          <input
            readOnly
            value={url || "No dashboard loaded"}
            style={{
              flex: 1,
              padding: "5px 10px",
              borderRadius: 6,
              border: "1px solid var(--ios-separator)",
              background: "transparent",
              color: "inherit",
              fontSize: 11,
              minWidth: 0,
            }}
          />

          <button
            onClick={() => setExpanded((v) =>!v)}
            className="ios-btn-ghost"
            style={{
              padding: "5px 12px",
              fontSize: 12,
              borderRadius: "var(--radius-pill)",
              cursor: "pointer",
            }}
          >
            {expanded ? "Collapse" : "Expand"}
          </button>

          <button
            onClick={handleEdit}
            disabled={importing || !metabaseId}
            className="ios-btn-ghost"
            style={{
              padding: "5px 12px",
              fontSize: 12,
              borderRadius: "var(--radius-pill)",
              cursor: metabaseId ? "pointer" : "not-allowed",
              opacity: importing ? 0.6 : 1,
            }}
          >
            {importing ? "..." : "Edit"}
          </button>

          {url && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="ios-btn-ghost"
              style={{
                padding: "5px 12px",
                fontSize: 12,
                borderRadius: "var(--radius-pill)",
                textDecoration: "none",
                color: "var(--ios-blue)",
              }}
            >
              Open
            </a>
          )}

          {onClose && (
            <button
              onClick={onClose}
              style={{
                width: 24,
                height: 24,
                borderRadius: "50%",
                border: "none",
                background: "transparent",
                color: "inherit",
                fontSize: 14,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              ×
            </button>
          )}
        </div>

        {error && (
          <div
            style={{
              padding: "6px 12px",
              color: "var(--ios-red)",
              fontSize: 11,
              background: "rgba(255, 59, 48, 0.08)",
              borderBottom: "1px solid var(--ios-separator)",
            }}
          >
            {error}
          </div>
        )}

        <div
          style={{
            flex: 1,
            background: "var(--ios-bg)",
            overflow: "auto",
            borderBottomLeftRadius: expanded ? 12 : 0,
            borderBottomRightRadius: expanded? 12 : 0,
          }}
        >
          {url ? (
            expanded ? (
              <iframe
                src={url}
                title="Metabase Dashboard"
                style={{ width: "100%", height: "100%", border: "none" }}
              />
            ) : (
              <div
                style={{
                  width: PANEL_WIDTH,
                  height: "100%",
                  overflow: "auto",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    width: RENDER_WIDTH,
                    height: `${100 / SCALE}%`,
                    transform: `scale(${SCALE})`,
                    transformOrigin: "top left",
                  }}
                >
                  <iframe
                    src={url}
                    title="Metabase Dashboard"
                    style={{
                      width: RENDER_WIDTH,
                      height: "100%",
                      border: "none",
                    }}
                  />
                </div>
              </div>
            )
          ) : (
            <div
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--ios-text-secondary)",
                fontSize: 12,
                padding: 24,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6, color: "var(--ios-text)" }}>
                No dashboard yet
              </div>
              <div>
                Ask BIthere to build one, for example:
                <br />
                "build a monthly trend dashboard with top 10 categories"
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}