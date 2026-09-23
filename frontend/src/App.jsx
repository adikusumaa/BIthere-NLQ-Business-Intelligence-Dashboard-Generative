import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Admin from "./pages/Admin.jsx";
import Chat from "./pages/Chat.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import SetupWizard from "./pages/wizard/SetupWizard.jsx";
import IntegrationsPage from "./pages/integrations/IntegrationsPage.jsx";
import DatasetsPage from "./pages/datasets/DatasetsPage.jsx";
import SchemaBuilderPage from "./pages/schema-builder/SchemaBuilderPage.jsx";
import KnowledgeBasePage from "./pages/knowledge-base/KnowledgeBasePage.jsx";
import DashboardEditorPage from "./pages/dashboard-editor/DashboardEditorPage.jsx";
import { useAuthStore } from "./store/authStore";
import { useWorkspaceStore } from "./store/workspaceStore";


function LoadingScreen() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--ios-text-secondary)",
        fontSize: "15px",
        background: "var(--ios-bg)",
      }}
    >
      Loading...
    </div>
  );
}


function ProtectedRoute({ children }) {
  const user = useAuthStore((s) => s.user);
  const loading = useAuthStore((s) => s.loading);
  const loadWorkspaces = useWorkspaceStore((s) => s.loadWorkspaces);

  useEffect(() => {
    if (user) loadWorkspaces();
  }, [user, loadWorkspaces]);

  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}


function WorkspaceGuard({ children }) {
  const user = useAuthStore((s) => s.user);
  const loading = useAuthStore((s) => s.loading);
  const wsLoading = useWorkspaceStore((s) => s.loading);
  const wsInitialized = useWorkspaceStore((s) => s.initialized);
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const loadWorkspaces = useWorkspaceStore((s) => s.loadWorkspaces);

  useEffect(() => {
    if (user) loadWorkspaces();
  }, [user, loadWorkspaces]);

  if (loading || wsLoading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" replace />;
  if (!wsInitialized) return <LoadingScreen />;

  if (!activeWorkspace) return <Navigate to="/wizard" replace />;
  if (!activeWorkspace.setup_completed) return <Navigate to="/wizard" replace />;

  return children;
}


function AdminRoute({ children }) {
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);
  const loading = useAuthStore((s) => s.loading);

  if (loading) return <LoadingScreen />;
  if (!user) return <Navigate to="/login" replace />;
  if (role !== "admin") return <Navigate to="/chat" replace />;
  return children;
}


export default function App() {
  const init = useAuthStore((s) => s.init);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/wizard"
        element={
          <ProtectedRoute>
            <SetupWizard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/integrations"
        element={
          <WorkspaceGuard>
            <IntegrationsPage />
          </WorkspaceGuard>
        }
      />

      <Route
        path="/datasets"
        element={
          <WorkspaceGuard>
            <DatasetsPage />
          </WorkspaceGuard>
        }
      />

      <Route
        path="/schema-builder"
        element={
          <WorkspaceGuard>
            <SchemaBuilderPage />
          </WorkspaceGuard>
        }
      />

      <Route
        path="/knowledge-base"
        element={
          <WorkspaceGuard>
            <KnowledgeBasePage />
          </WorkspaceGuard>
        }
      />

      <Route
        path="/dashboard/:id/edit"
        element={
          <WorkspaceGuard>
            <DashboardEditorPage />
          </WorkspaceGuard>
        }
      />

      <Route
        path="/chat"
        element={
          <WorkspaceGuard>
            <Chat />
          </WorkspaceGuard>
        }
      />

      <Route
        path="/admin"
        element={
          <AdminRoute>
            <Admin />
          </AdminRoute>
        }
      />

      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}