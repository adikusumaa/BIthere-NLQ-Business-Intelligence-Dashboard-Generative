import { useEffect, useState } from "react";
import { useWorkspaceStore } from "../store/workspaceStore";

export default function WorkspaceSwitcher() {
  const workspaces = useWorkspaceStore((s) => s.workspaces);
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const setActive = useWorkspaceStore((s) => s.setActive);
  const createWorkspace = useWorkspaceStore((s) => s.createWorkspace);

  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [open]);

  const handleCreate = async () => {
    const name = prompt("New workspace name:");
    if (!name) return;
    setCreating(true);
    try {
      await createWorkspace(name);
    } catch (err) {
      alert("Failed to create: " + err.message);
    } finally {
      setCreating(false);
      setOpen(false);
    }
  };

  return (
    <div style={{ position: "relative" }} onClick={(e) => e.stopPropagation()}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "6px 12px",
          borderRadius: 8,
          border: "1px solid var(--ios-separator)",
          background: "var(--ios-surface)",
          color: "inherit",
          fontSize: 13,
          cursor: "pointer",
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: activeWorkspace?.setup_completed ? "#10b981" : "#f59e0b",
          }}
        />
        <span style={{ maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {activeWorkspace?.name || "No workspace"}
        </span>
        <span style={{ fontSize: 9, opacity: 0.6 }}>▼</span>
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            right: 0,
            background: "var(--ios-surface)",
            border: "1px solid var(--ios-separator)",
            borderRadius: 10,
            minWidth: 240,
            padding: 6,
            boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
            zIndex: 100,
          }}
        >
          {workspaces.map((ws) => (
            <button
              key={ws.id}
              onClick={() => {
                setActive(ws);
                setOpen(false);
              }}
              style={{
                display: "flex",
                justifyContent: "space-between",
                width: "100%",
                padding: "8px 12px",
                background: ws.id === activeWorkspace?.id ? "rgba(59,130,246,0.1)" : "transparent",
                border: "none",
                borderRadius: 6,
                color: "inherit",
                fontSize: 13,
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <span>{ws.name}</span>
              {ws.setup_completed && <span style={{ color: "#10b981", fontSize: 11 }}>✓</span>}
            </button>
          ))}

          <div style={{ borderTop: "1px solid var(--ios-separator)", margin: "6px 0" }} />

          <button
            onClick={handleCreate}
            disabled={creating}
            style={{
              width: "100%",
              padding: "8px 12px",
              background: "transparent",
              border: "none",
              borderRadius: 6,
              color: "var(--ios-blue)",
              fontSize: 13,
              cursor: "pointer",
              textAlign: "left",
            }}
          >
            {creating ? "Creating..." : "+ New workspace"}
          </button>
        </div>
      )}
    </div>
  );
}