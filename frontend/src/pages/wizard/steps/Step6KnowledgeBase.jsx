import { useState } from "react";
import { api } from "../../../services/api";
import { useWorkspaceStore } from "../../../store/workspaceStore";
import { useWizardStore } from "../../../store/wizardStore";

export default function Step6KnowledgeBase({ onBack }) {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const saveStep = useWizardStore((s) => s.saveStep);
  const complete = useWizardStore((s) => s.complete);
  const resetStore = useWizardStore((s) => s.reset);

  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [adding, setAdding] = useState(false);
  const [reingesting, setReingesting] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleAddTerm = async () => {
    if (!term || !definition) return;
    setError(null);
    setAdding(true);
    try {
      await api.addGlossaryTerm(activeWorkspace.id, { term, definition });
      setTerm("");
      setDefinition("");
      setStatus("Term added. Re-ingest to make it searchable.");
    } catch (err) {
      setError(err.message);
    } finally {
      setAdding(false);
    }
  };

  const handleReingest = async () => {
    setError(null);
    setReingesting(true);
    setStatus(null);
    try {
      const res = await api.reingest(activeWorkspace.id);
      setStatus(`Ingested: schema=${res.schema.vectors}, glossary=${res.glossary.vectors}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setReingesting(false);
    }
  };

  const handleFinish = async () => {
    setError(null);
    try {
      await saveStep(activeWorkspace.id, 6, {});
      await complete(activeWorkspace.id);

      // Force reload workspaces from backend so setup_completed=true
      await useWorkspaceStore.getState().loadWorkspaces();

      resetStore();
      window.location.href = "/chat";
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>Step 6 — Knowledge Base</h2>
      <p style={{ color: "var(--ios-text-secondary)", marginBottom: 20, fontSize: 14 }}>
        Add optional glossary terms to help the AI understand domain-specific words.
      </p>

      <label style={labelStyle}>Term</label>
      <input value={term} onChange={(e) => setTerm(e.target.value)} style={inputStyle} placeholder="e.g. chargeback" />

      <label style={labelStyle}>Definition</label>
      <textarea
        value={definition}
        onChange={(e) => setDefinition(e.target.value)}
        rows={3}
        style={{ ...inputStyle, resize: "vertical" }}
        placeholder="A reversal of a card transaction initiated by the cardholder or issuer..."
      />

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={handleAddTerm} disabled={adding || !term || !definition} style={btnStyle("#6b7280")}>
          {adding ? "..." : "Add Term"}
        </button>
        <button onClick={handleReingest} disabled={reingesting} style={btnStyle("#10b981")}>
          {reingesting ? "..." : "Re-ingest to Pinecone"}
        </button>
      </div>

      {status && <div style={{ color: "#10b981", marginTop: 12, fontSize: 13 }}>{status}</div>}
      {error && <div style={{ color: "#f87171", marginTop: 12, fontSize: 13 }}>{error}</div>}

      <div style={{ display: "flex", gap: 8, marginTop: 24 }}>
        <button onClick={onBack} style={btnStyle("#6b7280")}>Back</button>
        <button onClick={handleFinish} style={btnStyle("#3b82f6")}>Finish & Go to Chat</button>
      </div>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 13, marginBottom: 6, marginTop: 12 };
const inputStyle = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: 6,
  border: "1px solid #374151",
  background: "transparent",
  color: "inherit",
  fontSize: 13,
};
function btnStyle(bg) {
  return { padding: "8px 16px", borderRadius: 6, border: "none", background: bg, color: "white", fontSize: 13, cursor: "pointer" };
}