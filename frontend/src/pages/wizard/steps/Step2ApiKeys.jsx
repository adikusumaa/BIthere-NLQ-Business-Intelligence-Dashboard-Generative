import { useEffect, useState } from "react";
import { api } from "../../../services/api";
import { useWorkspaceStore } from "../../../store/workspaceStore";
import { useWizardStore } from "../../../store/wizardStore";

const SERVICES = [
  { key: "groq", label: "Groq (LLM)", hint: "gsk_..." },
  { key: "google", label: "Google AI (Embedding)", hint: "AIza..." },
  { key: "pinecone", label: "Pinecone (Vector DB)", hint: "pcsk_..." },
];

export default function Step2ApiKeys({ onNext, onBack }) {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const saveStep = useWizardStore((s) => s.saveStep);

  const [values, setValues] = useState({ groq: "", google: "", pinecone: "" });
  const [configured, setConfigured] = useState({});
  const [testing, setTesting] = useState({});
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const list = await api.listIntegrations(activeWorkspace.id);
        const map = {};
        for (const item of list) {
          if (item.configured) map[item.service] = true;
        }
        setConfigured(map);
      } catch (err) {
        setError(err.message);
      }
    })();
  }, [activeWorkspace.id]);

  const handleSave = async (service) => {
    setError(null);
    try {
      await api.setIntegration(activeWorkspace.id, service, values[service], {});
      setConfigured((c) => ({ ...c, [service]: true }));
      setValues((v) => ({ ...v, [service]: "" }));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleTest = async (service) => {
    setTesting((t) => ({ ...t, [service]: true }));
    try {
      const res = await api.testIntegration(activeWorkspace.id, service, {});
      setResults((r) => ({ ...r, [service]: res }));
    } catch (err) {
      setResults((r) => ({ ...r, [service]: { ok: false, message: err.message } }));
    } finally {
      setTesting((t) => ({ ...t, [service]: false }));
    }
  };

  const handleContinue = async () => {
    if (!configured.groq) {
      setError("At least Groq API key is required to continue");
      return;
    }
    await saveStep(activeWorkspace.id, 2, { services: Object.keys(configured) });
    onNext();
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>Step 2 — API Keys</h2>
      <p style={{ color: "var(--ios-text-secondary)", marginBottom: 20, fontSize: 14 }}>
        Bring your own keys. They are encrypted at rest and never shown again.
      </p>

      {SERVICES.map((svc) => (
        <div
          key={svc.key}
          style={{
            border: "1px solid #374151",
            borderRadius: 8,
            padding: 16,
            marginBottom: 12,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <strong style={{ fontSize: 14 }}>{svc.label}</strong>
            {configured[svc.key] && (
              <span style={{ color: "#10b981", fontSize: 12 }}>✓ configured</span>
            )}
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="password"
              placeholder={svc.hint}
              value={values[svc.key]}
              onChange={(e) =>
                setValues((v) => ({ ...v, [svc.key]: e.target.value }))
              }
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #374151",
                background: "transparent",
                color: "inherit",
                fontSize: 13,
              }}
            />
            <button
              onClick={() => handleSave(svc.key)}
              disabled={!values[svc.key]}
              style={btnStyle("#3b82f6")}
            >
              Save
            </button>
            <button
              onClick={() => handleTest(svc.key)}
              disabled={!configured[svc.key] || testing[svc.key]}
              style={btnStyle("#6b7280")}
            >
              {testing[svc.key] ? "..." : "Test"}
            </button>
          </div>

          {results[svc.key] && (
            <div
              style={{
                marginTop: 8,
                fontSize: 12,
                color: results[svc.key].ok ? "#10b981" : "#f87171",
              }}
            >
              {results[svc.key].ok ? "OK: " : "Failed: "}
              {results[svc.key].message}
            </div>
          )}
        </div>
      ))}

      {error && <div style={{ color: "#f87171", marginBottom: 12, fontSize: 13 }}>{error}</div>}

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={onBack} style={btnStyle("#6b7280")}>Back</button>
        <button
          onClick={handleContinue}
          disabled={!configured.groq}
          style={btnStyle("#3b82f6")}
        >
          Save & Continue
        </button>
      </div>
    </div>
  );
}

function btnStyle(bg) {
  return {
    padding: "8px 16px",
    borderRadius: 6,
    border: "none",
    background: bg,
    color: "white",
    fontSize: 13,
    cursor: "pointer",
  };
}