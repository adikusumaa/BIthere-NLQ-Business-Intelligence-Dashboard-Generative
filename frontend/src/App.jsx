import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import Admin from "./pages/Admin.jsx";
import Chat from "./pages/Chat.jsx";
import Login from "./pages/Login.jsx";
import SetupWizard from "./pages/wizard/SetupWizard.jsx";
import IntegrationsPage from "./pages/integrations/IntegrationsPage.jsx";
import DatasetsPage from "./pages/datasets/DatasetsPage.jsx";
import SchemaBuilderPage from "./pages/schema-builder/SchemaBuilderPage.jsx";
import KnowledgeBasePage from "./pages/knowledge-base/KnowledgeBasePage.jsx";
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
          <ProtectedRoute>
            <IntegrationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/datasets"
        element={
          <ProtectedRoute>
            <DatasetsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/schema-builder"
        element={
          <ProtectedRoute>
            <SchemaBuilderPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/knowledge-base"
        element={
          <ProtectedRoute>
            <KnowledgeBasePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
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