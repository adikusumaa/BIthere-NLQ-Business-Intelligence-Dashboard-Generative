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
    <div style={{ minHeight: "100vh", padding: "32px 24px 60px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <header style={{ marginBottom: 28 }}>
          <h1
            style={{
              fontSize: 34,
              fontWeight: 700,
              letterSpacing: "-0.03em",
              color: "var(--ios-text)",
              marginBottom: 4,
            }}
          >
            Knowledge Base
          </h1>
          <p style={{ fontSize: 15, color: "var(--ios-text-secondary)" }}>
            Manage the metadata that powers AI retrieval.
          </p>
        </header>

        <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className="ios-btn ios-btn-pill"
              style={{
                padding: "8px 18px",
                fontSize: 14,
                fontWeight: 600,
                background: tab === t.id ? "var(--ios-blue)" : "var(--ios-surface)",
                color: tab === t.id ? "#FFFFFF" : "var(--ios-text)",
                border: "1px solid",
                borderColor: tab === t.id ? "var(--ios-blue)" : "var(--ios-separator)",
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