import { useState } from "react";
import { api } from "../../services/api";

export default function ChatPanel({ workspaceId, dashboardId, currentState, onApplied, sessionId }) {
  const [instruction, setInstruction] = useState("");
  const [parsing, setParsing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [parsed, setParsed] = useState(null);
  const [error, setError] = useState(null);
  const [messages, setMessages] = useState([]);

  const addMessage = (role, text, extra = {}) => {
    setMessages((prev) => [...prev, { role, text, ...extra, ts: Date.now() }]);
  };

  const handleParse = async () => {
    if (!instruction.trim()) return;
    setError(null);
    setParsed(null);
    setParsing(true);

    const text = instruction;
    addMessage("user", text);
    setInstruction("");

    try {
      const res = await api.parseDashboardPatch(workspaceId, dashboardId, text);
      setParsed(res);
      addMessage("assistant", `Proposed: ${res.patch?.patch_type || "unknown"}`, {
        patch: res.patch,
        validation: res.validation,
      });
    } catch (err) {
      setError(err.message);
      addMessage("assistant", `Error: ${err.message}`);
    } finally {
      setParsing(false);
    }
  };

  const handleApply = async () => {
    if (!parsed) return;
    setError(null);
    setApplying(true);
    try {
      const res = await api.applyDashboardPatch(workspaceId, dashboardId, {
        patch: parsed.patch,
        base_version: currentState.version,
      });
      addMessage("assistant", `Applied ✓ version ${res.version}`, { applied: true });
      setParsed(null);
      if (onApplied) onApplied(res.state);
    } catch (err) {
      setError(err.message);
      addMessage("assistant", `Apply failed: ${err.message}`);
    } finally {
      setApplying(false);
    }
  };

  const handleReject = () => {
    setParsed(null);
    addMessage("assistant", "Patch rejected.");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--ios-separator)" }}>
        <strong style={{ fontSize: 13 }}>Dashboard Editor Chat</strong>
        <div style={{ fontSize: 11, color: "var(--ios-text-secondary)", marginTop: 2 }}>
          State version: v{currentState?.version}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
        {messages.length === 0 && (
          <div style={{ fontSize: 12, color: "var(--ios-text-tertiary)", textAlign: "center", marginTop: 20 }}>
            Try: "Ubah warna Total Amount jadi merah"<br />
            or: "Hapus Amount by City"
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              padding: "8px 12px",
              borderRadius: 10,
              background: m.role === "user" ? "#3b82f6" : "rgba(255,255,255,0.05)",
              color: m.role === "user" ? "white" : "inherit",
              fontSize: 12,
              lineHeight: 1.4,
            }}
          >
            <div>{m.text}</div>

            {m.validation && !m.validation.valid && (
              <div style={{ marginTop: 4, fontSize: 11, color: "#f87171" }}>
                ⚠ {m.validation.reason}
              </div>
            )}

            {m.patch && (
              <details style={{ marginTop: 6 }}>
                <summary style={{ cursor: "pointer", fontSize: 11, opacity: 0.8 }}>
                  View patch JSON
                </summary>
                <pre style={{ marginTop: 4, fontSize: 10, maxHeight: 200, overflow: "auto", background: "rgba(0,0,0,0.2)", padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(m.patch, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>

      {parsed && (
        <div
          style={{
            padding: 12,
            borderTop: "1px solid var(--ios-separator)",
            background: "rgba(59,130,246,0.08)",
            display: "flex",
            gap: 8,
          }}
        >
          <button onClick={handleApply} disabled={applying} style={btn("#10b981")}>
            {applying ? "..." : "Apply"}
          </button>
          <button onClick={handleReject} style={btn("#6b7280")}>
            Reject
          </button>
        </div>
      )}

      {error && (
        <div style={{ padding: "8px 12px", fontSize: 11, color: "#f87171", borderTop: "1px solid var(--ios-separator)" }}>
          {error}
        </div>
      )}

      <div style={{ padding: 12, borderTop: "1px solid var(--ios-separator)" }}>
        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleParse();
            }
          }}
          placeholder="Describe your change..."
          rows={2}
          disabled={parsing}
          style={{
            width: "100%",
            padding: "8px 10px",
            borderRadius: 6,
            border: "1px solid var(--ios-separator)",
            background: "transparent",
            color: "inherit",
            fontSize: 12,
            resize: "vertical",
            fontFamily: "inherit",
          }}
        />
        <button
          onClick={handleParse}
          disabled={parsing || !instruction.trim()}
          style={{ ...btn("#3b82f6"), marginTop: 8, width: "100%" }}
        >
          {parsing ? "Parsing..." : "Parse & Preview"}
        </button>
      </div>
    </div>
  );
}

function btn(bg) {
  return {
    padding: "7px 14px",
    borderRadius: 6,
    border: "none",
    background: bg,
    color: "white",
    fontSize: 12,
    cursor: "pointer",
  };
}