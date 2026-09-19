import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Navbar from "../../components/Navbar";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

import ChatPanel from "../../components/dashboard-editor/ChatPanel";
import LivePreview from "../../components/dashboard-editor/LivePreview";
import PatchHistoryPanel from "../../components/dashboard-editor/PatchHistoryPanel";
import PropertyPanel from "../../components/dashboard-editor/PropertyPanel";
import UndoRedoBar from "../../components/dashboard-editor/UndoRedoBar";

export default function DashboardEditorPage() {
  const { id: dashboardId } = useParams();
  const navigate = useNavigate();
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);

  const [state, setState] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCardId, setSelectedCardId] = useState(null);
  const [sessionId] = useState(() => `edit-${Math.random().toString(36).slice(2)}`);

  const loadState = async () => {
    if (!activeWorkspace?.id || !dashboardId) return;
    setLoading(true);
    setError(null);
    try {
      const [st, h] = await Promise.all([
        api.getDashboardState(activeWorkspace.id, dashboardId),
        api.listDashboardVersions(activeWorkspace.id, dashboardId),
      ]);
      setState(st);
      setHistory(h);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadState();
  }, [activeWorkspace?.id, dashboardId]);

  const refreshAfterChange = async (newState) => {
    setState(newState);
    const h = await api.listDashboardVersions(activeWorkspace.id, dashboardId);
    setHistory(h);
  };

  if (!activeWorkspace) return <div style={{ padding: 32 }}>No workspace selected</div>;
  if (!dashboardId) return <div style={{ padding: 32 }}>No dashboard id in URL</div>;
  if (loading) return <div style={{ padding: 32 }}>Loading dashboard...</div>;
  if (error) return <div style={{ padding: 32, color: "#f87171" }}>{error}</div>;

  return (
    <div style={{ minHeight: "100vh", background: "var(--ios-bg)" }}>
      <Navbar />
      <UndoRedoBar
        workspaceId={activeWorkspace.id}
        dashboardId={dashboardId}
        sessionId={sessionId}
        onChanged={refreshAfterChange}
      />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "380px 1fr 280px",
          gap: 12,
          padding: 12,
          height: "calc(100vh - 100px)",
          overflow: "hidden",
        }}
      >
        <div style={{ overflow: "auto", border: "1px solid var(--ios-separator)", borderRadius: 10, background: "var(--ios-surface)" }}>
          <ChatPanel
            workspaceId={activeWorkspace.id}
            dashboardId={dashboardId}
            currentState={state}
            onApplied={refreshAfterChange}
            sessionId={sessionId}
          />
        </div>

        <div style={{ overflow: "auto", border: "1px solid var(--ios-separator)", borderRadius: 10, background: "var(--ios-surface)" }}>
          <LivePreview
            workspaceId={activeWorkspace.id}
            dashboardId={dashboardId}
            state={state}
            selectedCardId={selectedCardId}
            onSelectCard={setSelectedCardId}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12, overflow: "auto" }}>
          <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, background: "var(--ios-surface)", flex: 1, overflow: "auto" }}>
            <PropertyPanel
              workspaceId={activeWorkspace.id}
              dashboardId={dashboardId}
              state={state}
              selectedCardId={selectedCardId}
              sessionId={sessionId}
              onApplied={refreshAfterChange}
            />
          </div>
          <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, background: "var(--ios-surface)", flex: 1, overflow: "auto" }}>
            <PatchHistoryPanel
              workspaceId={activeWorkspace.id}
              dashboardId={dashboardId}
              history={history}
              currentVersion={state?.version}
              onRolledBack={refreshAfterChange}
            />
          </div>
        </div>
      </div>
    </div>
  );
}