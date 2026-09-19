import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

const SERVICES = [
  { key: "groq", label: "Groq (LLM)", hint: "gsk_...", required: true },
  { key: "google", label: "Google AI (Embedding)", hint: "AIza..." },
  { key: "pinecone", label: "Pinecone (Vector DB)", hint: "pcsk_..." },
  { key: "metabase", label: "Metabase", hint: "session token / password" },
  { key: "slack", label: "Slack Webhook", hint: "https://hooks.slack.com/..." },
  { key: "email", label: "Email (Resend/SMTP)", hint: "re_..." },
];

export default function IntegrationsPage() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [busy, setBusy] = useState(null);
  const [testResults, setTestResults] = useState({});

  const load = async () => {
    if (!activeWorkspace?.id) return;
    setLoading(true);
    setError(null);
    try {
      const list = await api.listIntegrations(activeWorkspace.id);
      setIntegrations(list);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [activeWorkspace?.id]);

  const handleSave = async (service) => {
    setError(null);
    setBusy(service);
    try {
      await api.setIntegration(activeWorkspace.id, service, inputValue);
      setEditing(null);
      setInputValue("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  const handleTest = async (service) => {
    setBusy(service);
    setTestResults((r) => ({ ...r, [service]: null }));
    try {
      const res = await api.testIntegration(activeWorkspace.id, service, {});
      setTestResults((r) => ({ ...r, [service]: res }));
    } catch (err) {
      setTestResults((r) => ({ ...r, [service]: { ok: false, message: err.message } }));
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async (service) => {
    if (!confirm(`Delete API key for ${service}?`)) return;
    setBusy(service);
    try {
      await api.deleteIntegration(activeWorkspace.id, service);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  };

  const configuredMap = Object.fromEntries(
    integrations.map((i) => [i.service, i])
  );

  if (!activeWorkspace) {
    return <div style={{ padding: 32 }}>No workspace selected</div>;
  }

  return (
    <div style={{ minHeight: "100vh", padding: "32px 24px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <header style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>Integrations</h1>
          <p style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>
            Bring your own keys. They are encrypted at rest.
          </p>
        </header>

        {error && (
          <div
            style={{
              color: "#f87171",
              background: "rgba(248,113,113,0.08)",
              padding: "10px 14px",
              borderRadius: 8,
              marginBottom: 16,
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}

        {loading && <div style={{ color: "var(--ios-text-secondary)" }}>Loading...</div>}

        {!loading &&
          SERVICES.map((svc) => {
            const info = configuredMap[svc.key];
            const configured = Boolean(info?.configured);
            const editing_ = editing === svc.key;
            const result = testResults[svc.key];

            return (
              <div
                key={svc.key}
                style={{
                  border: "1px solid var(--ios-separator)",
                  borderRadius: 10,
                  padding: 16,
                  marginBottom: 12,
                  background: "var(--ios-surface)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                  <div>
                    <strong style={{ fontSize: 14 }}>{svc.label}</strong>
                    {svc.required && (
                      <span style={{ fontSize: 11, marginLeft: 8, color: "var(--ios-text-secondary)" }}>
                        required
                      </span>
                    )}
                  </div>
                  {configured ? (
                    <span style={{ color: "#10b981", fontSize: 12 }}>✓ configured</span>
                  ) : (
                    <span style={{ color: "var(--ios-text-tertiary)", fontSize: 12 }}>
                      not set
                    </span>
                  )}
                </div>

                {!editing_ && (
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button onClick={() => { setEditing(svc.key); setInputValue(""); }} style={btn("#3b82f6")}>
                      {configured ? "Rotate" : "Set key"}
                    </button>
                    <button
                      onClick={() => handleTest(svc.key)}
                      disabled={!configured || busy === svc.key}
                      style={btn("#6b7280")}
                    >
                      {busy === svc.key ? "..." : "Test"}
                    </button>
                    {configured && (
                      <button
                        onClick={() => handleDelete(svc.key)}
                        disabled={busy === svc.key}
                        style={btn("#ef4444")}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                )}

                {editing_ && (
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="password"
                      placeholder={svc.hint}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      autoFocus
                      style={{
                        flex: 1,
                        padding: "8px 12px",
                        borderRadius: 6,
                        border: "1px solid var(--ios-separator)",
                        background: "transparent",
                        color: "inherit",
                        fontSize: 13,
                      }}
                    />
                    <button
                      onClick={() => handleSave(svc.key)}
                      disabled={!inputValue || busy === svc.key}
                      style={btn("#10b981")}
                    >
                      {busy === svc.key ? "..." : "Save"}
                    </button>
                    <button
                      onClick={() => { setEditing(null); setInputValue(""); }}
                      style={btn("#6b7280")}
                    >
                      Cancel
                    </button>
                  </div>
                )}

                {result && (
                  <div
                    style={{
                      marginTop: 10,
                      fontSize: 12,
                      color: result.ok ? "#10b981" : "#f87171",
                    }}
                  >
                    {result.ok ? "OK: " : "Failed: "}
                    {result.message}
                  </div>
                )}
              </div>
            );
          })}
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
    fontSize: 13,
    cursor: "pointer",
  };
}