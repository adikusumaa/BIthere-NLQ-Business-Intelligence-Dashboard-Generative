import { useState } from "react";
import { api } from "../../../services/api";
import { useWorkspaceStore } from "../../../store/workspaceStore";
import { useWizardStore } from "../../../store/wizardStore";

const DB_TYPES = [
  { key: "postgresql", label: "PostgreSQL / Supabase" },
  { key: "mysql", label: "MySQL / MariaDB" },
  { key: "mongodb", label: "MongoDB" },
  { key: "sqlite", label: "SQLite (file)" },
  { key: "duckdb", label: "DuckDB (file)" },
];

const DEFAULT_PORTS = {
  postgresql: 5432,
  mysql: 3306,
  mongodb: 27017,
};

export default function Step3DataSource({ onNext, onBack }) {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const saveStep = useWizardStore((s) => s.saveStep);

  const [dsType, setDsType] = useState("sqlite");
  const [name, setName] = useState("Local DB");
  const [form, setForm] = useState({
    connection: ":memory:",
    host: "",
    port: "",
    database: "",
    username: "",
    password: "",
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState(null);
  const [createdDsId, setCreatedDsId] = useState(null);

  const isFilePath = dsType === "sqlite" || dsType === "duckdb";
  const isConnectionString = dsType === "mongodb";

  const handleSubmit = async (test = false) => {
    setError(null);
    setTestResult(null);
    setSaving(true);
    try {
      const payload = {
        name,
        type: dsType,
        is_default: true,
      };

      if (isFilePath || isConnectionString) {
        payload.connection = form.connection;
      } else {
        payload.connection = form.connection || null;
        payload.host = form.host || null;
        payload.port = form.port ? Number(form.port) : DEFAULT_PORTS[dsType];
        payload.database = form.database || null;
        payload.username = form.username || null;
        payload.password = form.password || null;
      }

      const ds = await api.addDataSource(activeWorkspace.id, payload);
      setCreatedDsId(ds.id);

      if (test) {
        setTesting(true);
        const res = await api.testDataSource(activeWorkspace.id, ds.id);
        setTestResult(res);
        setTesting(false);
        if (!res.ok) return;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleContinue = async () => {
    if (!createdDsId) {
      setError("Save the data source first");
      return;
    }
    await saveStep(activeWorkspace.id, 3, { ds_id: createdDsId, type: dsType });
    onNext();
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>Step 3 — Data Source</h2>
      <p style={{ color: "var(--ios-text-secondary)", marginBottom: 20, fontSize: 14 }}>
        Choose where your data lives. For uploaded files, choose DuckDB or SQLite.
      </p>

      <label style={labelStyle}>Type</label>
      <select
        value={dsType}
        onChange={(e) => {
          const t = e.target.value;
          setDsType(t);
          setCreatedDsId(null);
          setTestResult(null);
          if (t === "sqlite") setForm({ ...form, connection: ":memory:" });
          else if (t === "duckdb") setForm({ ...form, connection: "" });
          else setForm({ connection: "", host: "", port: DEFAULT_PORTS[t] || "", database: "", username: "", password: "" });
        }}
        style={inputStyle}
      >
        {DB_TYPES.map((t) => (
          <option key={t.key} value={t.key}>{t.label}</option>
        ))}
      </select>

      <label style={labelStyle}>Name</label>
      <input value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />

      {(isFilePath || isConnectionString) ? (
        <>
          <label style={labelStyle}>
            {isFilePath ? "File path" : "Connection string"}
          </label>
          <input
            value={form.connection}
            onChange={(e) => setForm({ ...form, connection: e.target.value })}
            placeholder={isFilePath ? "/app/duckdb/workspace.duckdb" : "mongodb://user:pass@host:27017"}
            style={inputStyle}
          />
        </>
      ) : (
        <>
          <label style={labelStyle}>Connection string (optional — overrides host/port below)</label>
          <input
            value={form.connection}
            onChange={(e) => setForm({ ...form, connection: e.target.value })}
            placeholder="postgresql://user:pass@host:5432/db"
            style={inputStyle}
          />
          <label style={labelStyle}>Host</label>
          <input value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })} style={inputStyle} />
          <label style={labelStyle}>Port</label>
          <input value={form.port} onChange={(e) => setForm({ ...form, port: e.target.value })} style={inputStyle} />
          <label style={labelStyle}>Database</label>
          <input value={form.database} onChange={(e) => setForm({ ...form, database: e.target.value })} style={inputStyle} />
          <label style={labelStyle}>Username</label>
          <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} style={inputStyle} />
          <label style={labelStyle}>Password</label>
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={inputStyle} />
        </>
      )}

      {error && <div style={{ color: "#f87171", marginBottom: 12, fontSize: 13 }}>{error}</div>}
      {testResult && (
        <div style={{ color: testResult.ok ? "#10b981" : "#f87171", marginBottom: 12, fontSize: 13 }}>
          {testResult.ok ? "OK: " : "Failed: "}{testResult.message}
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <button onClick={onBack} style={btnStyle("#6b7280")}>Back</button>
        <button onClick={() => handleSubmit(true)} disabled={saving || testing} style={btnStyle("#10b981")}>
          {saving || testing ? "..." : "Save & Test"}
        </button>
        <button onClick={handleContinue} disabled={!createdDsId} style={btnStyle("#3b82f6")}>
          Save & Continue
        </button>
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