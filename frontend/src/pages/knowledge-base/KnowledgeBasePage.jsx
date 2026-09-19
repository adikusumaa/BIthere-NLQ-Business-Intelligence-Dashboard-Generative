import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";
import SchemaTab from "./SchemaTab.jsx";
import GlossaryTab from "./GlossaryTab.jsx";
import ReingestPanel from "./ReingestPanel.jsx";

const TABS = [
  { id: "schema", label: "Schema" },
  { id: "glossary", label: "Glossary" },
  { id: "reingest", label: "Re-ingest" },
];

export default function KnowledgeBasePage() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const [tab, setTab] = useState("schema");

  if (!activeWorkspace) {
    return <div style={{ padding: 32 }}>No workspace selected</div>;
  }

  return (
    <div style={{ minHeight: "100vh", padding: "32px 24px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <header style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>Knowledge Base</h1>
          <p style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>
            Manage the metadata that powers AI retrieval: schema, glossary, and re-ingestion.
          </p>
        </header>

        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: "8px 16px",
                borderRadius: 8,
                border: "1px solid",
                borderColor: tab === t.id ? "#3b82f6" : "var(--ios-separator)",
                background: tab === t.id ? "#3b82f6" : "transparent",
                color: tab === t.id ? "white" : "inherit",
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "schema" && <SchemaTab />}
        {tab === "glossary" && <GlossaryTab />}
        {tab === "reingest" && <ReingestPanel />}
      </div>
    </div>
  );
}