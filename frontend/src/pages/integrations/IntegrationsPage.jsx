import { useEffect, useState } from "react";
import ConfirmDialog from "../../components/ConfirmDialog";
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
  const [confirmService, setConfirmService] = useState(null);

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

  const handleDelete = (service) => {
    setConfirmService(service);
  };

  const confirmDeleteNow = async () => {
    const service = confirmService;
    setConfirmService(null);
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
    <div style={{ minHeight: "100vh", padding: "32px 24px 60px", background: "var(--ios-bg)" }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
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
            Integrations
          </h1>
          <p style={{ fontSize: 15, color: "var(--ios-text-secondary)" }}>
            Bring your own keys. They are encrypted at rest.
          </p>
        </header>

        {error && (
          <div
            style={{
              background: "rgba(255, 59, 48, 0.10)",
              color: "var(--ios-red)",
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              marginBottom: 16,
              fontSize: 14,
              border: "1px solid rgba(255, 59, 48, 0.24)",
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
                  background: "var(--ios-surface)",
                  borderRadius: "var(--radius-md)",
                  padding: "16px 20px",
                  marginBottom: 12,
                  border: "1px solid var(--ios-separator)",
                  boxShadow: "var(--shadow-xs)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 12,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                    <span style={{ fontSize: 16, fontWeight: 700, color: "var(--ios-text)" }}>
                      {svc.label}
                    </span>
                    {svc.required && (
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color: "var(--ios-text-secondary)",
                          textTransform: "uppercase",
                          letterSpacing: "0.04em",
                        }}
                      >
                        required
                      </span>
                    )}
                  </div>
                  {configured ? (
                    <span
                      style={{
                        color: "var(--ios-green)",
                        fontSize: 13,
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                      }}
                    >
                      ✓ configured
                    </span>
                  ) : (
                    <span style={{ color: "var(--ios-text-tertiary)", fontSize: 13 }}>
                      not set
                    </span>
                  )}
                </div>

                {!editing_ && (
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <button
                      onClick={() => {
                        setEditing(svc.key);
                        setInputValue("");
                      }}
                      className="ios-btn ios-btn-pill"
                      style={{
                        padding: "7px 18px",
                        fontSize: 14,
                        fontWeight: 600,
                        background: "var(--ios-blue)",
                        color: "#FFFFFF",
                      }}
                    >
                      {configured ? "Rotate" : "Set key"}
                    </button>
                    <button
                      onClick={() => handleTest(svc.key)}
                      disabled={!configured || busy === svc.key}
                      className="ios-btn ios-btn-pill"
                      style={{
                        padding: "7px 18px",
                        fontSize: 14,
                        fontWeight: 600,
                        background: "var(--ios-surface-2)",
                        color: "var(--ios-text)",
                        opacity: !configured ? 0.5 : 1,
                      }}
                    >
                      {busy === svc.key ? "Testing..." : "Test"}
                    </button>
                    {configured && (
                      <button
                        onClick={() => handleDelete(svc.key)}
                        disabled={busy === svc.key}
                        className="ios-btn ios-btn-pill"
                        style={{
                          padding: "7px 18px",
                          fontSize: 14,
                          fontWeight: 600,
                          background: "var(--ios-red)",
                          color: "#FFFFFF",
                        }}
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
                      className="ios-input"
                      style={{ flex: 1 }}
                    />
                    <button
                      onClick={() => handleSave(svc.key)}
                      disabled={!inputValue || busy === svc.key}
                      className="ios-btn ios-btn-pill"
                      style={{
                        padding: "9px 20px",
                        fontSize: 14,
                        fontWeight: 600,
                        background: "var(--ios-green)",
                        color: "#FFFFFF",
                      }}
                    >
                      {busy === svc.key ? "..." : "Save"}
                    </button>
                    <button
                      onClick={() => {
                        setEditing(null);
                        setInputValue("");
                      }}
                      className="ios-btn ios-btn-pill"
                      style={{
                        padding: "9px 20px",
                        fontSize: 14,
                        fontWeight: 600,
                        background: "var(--ios-surface-2)",
                        color: "var(--ios-text)",
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                )}

                {result && (
                  <div
                    style={{
                      marginTop: 12,
                      fontSize: 13,
                      color: result.ok ? "var(--ios-green)" : "var(--ios-red)",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <strong>{result.ok ? "OK" : "Failed"}:</strong>
                    <span>{result.message}</span>
                  </div>
                )}
              </div>
            );
          })}
      </div>

      <ConfirmDialog
        open={!!confirmService}
        title="Delete API key?"
        message={
          confirmService
            ? `The ${confirmService} key will be removed from this workspace. You can re-add it later.`
            : ""
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={confirmDeleteNow}
        onCancel={() => setConfirmService(null)}
      />
    </div>
  );
}