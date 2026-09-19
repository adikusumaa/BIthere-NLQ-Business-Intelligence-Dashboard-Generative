import { useState } from "react";
import { useWorkspaceStore } from "../../../store/workspaceStore";
import { useWizardStore } from "../../../store/wizardStore";

export default function Step1Account({ onNext }) {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const refreshWorkspace = useWorkspaceStore((s) => s.refreshWorkspace);
  const saveStep = useWizardStore((s) => s.saveStep);

  const [name, setName] = useState(activeWorkspace?.name || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSave = async () => {
    setError(null);
    setSaving(true);
    try {
      await saveStep(activeWorkspace.id, 1, { name });
      await refreshWorkspace(activeWorkspace.id);
      onNext();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>Step 1 — Account & Workspace</h2>
      <p style={{ color: "var(--ios-text-secondary)", marginBottom: 20, fontSize: 14 }}>
        Confirm your workspace name. You can change it later.
      </p>

      <label style={{ display: "block", fontSize: 13, marginBottom: 6 }}>Workspace name</label>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{
          width: "100%",
          padding: "10px 12px",
          borderRadius: 8,
          border: "1px solid #374151",
          background: "transparent",
          color: "inherit",
          fontSize: 14,
          marginBottom: 16,
        }}
      />

      {error && (
        <div style={{ color: "#f87171", marginBottom: 12, fontSize: 13 }}>{error}</div>
      )}

      <button
        onClick={handleSave}
        disabled={saving || !name.trim()}
        style={{
          padding: "10px 20px",
          borderRadius: 8,
          border: "none",
          background: "#3b82f6",
          color: "white",
          fontSize: 14,
          cursor: saving ? "wait" : "pointer",
        }}
      >
        {saving ? "Saving..." : "Save & Continue"}
      </button>
    </div>
  );
}