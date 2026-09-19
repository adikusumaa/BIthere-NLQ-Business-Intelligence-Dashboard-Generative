import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { useWorkspaceStore } from "../../store/workspaceStore";

export default function GlossaryTab() {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);

  const [terms, setTerms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [adding, setAdding] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const load = async () => {
    setLoading(true);
    try {
      const list = await api.listGlossary(activeWorkspace.id);
      setTerms(list);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [activeWorkspace.id]);

  const handleAdd = async () => {
    if (!term || !definition) return;
    setAdding(true);
    setError(null);
    try {
      await api.addGlossaryTerm(activeWorkspace.id, { term, definition });
      setTerm("");
      setDefinition("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this term?")) return;
    try {
      await api.deleteGlossaryTerm(activeWorkspace.id, id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCsv = async (file) => {
    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadGlossaryCsv(activeWorkspace.id, file);
      alert(`Imported ${res.imported} terms`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 16, background: "var(--ios-surface)", marginBottom: 20 }}>
        <strong style={{ fontSize: 14 }}>Add term</strong>
        <div style={{ marginTop: 12 }}>
          <input
            placeholder="Term (e.g. chargeback)"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            style={inputStyle}
          />
          <textarea
            placeholder="Definition..."
            value={definition}
            onChange={(e) => setDefinition(e.target.value)}
            rows={3}
            style={{ ...inputStyle, resize: "vertical" }}
          />
          <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
            <button onClick={handleAdd} disabled={adding || !term || !definition} style={btn("#10b981")}>
              {adding ? "..." : "Add Term"}
            </button>
            <button onClick={() => inputRef.current?.click()} disabled={uploading} style={btn("#6b7280")}>
              {uploading ? "..." : "Upload CSV"}
            </button>
            <input ref={inputRef} type="file" accept=".csv" style={{ display: "none" }}
              onChange={(e) => e.target.files?.[0] && handleCsv(e.target.files[0])} />
          </div>
          <div style={{ fontSize: 11, color: "var(--ios-text-tertiary)", marginTop: 8 }}>
            CSV columns: term,definition,category,synonyms (pipe-separated)
          </div>
        </div>
      </div>

      {error && <div style={{ color: "#f87171", marginBottom: 12, fontSize: 13 }}>{error}</div>}

      {loading && <div style={{ color: "var(--ios-text-secondary)" }}>Loading...</div>}
      {!loading && terms.length === 0 && (
        <div style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>No terms yet.</div>
      )}

      {terms.map((t) => (
        <div key={t.id} style={{ border: "1px solid var(--ios-separator)", borderRadius: 10, padding: 14, marginBottom: 8, background: "var(--ios-surface)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <strong style={{ fontSize: 14 }}>{t.term}</strong>
            <button onClick={() => handleDelete(t.id)} style={btn("#ef4444")}>Delete</button>
          </div>
          <div style={{ fontSize: 13, color: "var(--ios-text-secondary)" }}>{t.definition}</div>
          {t.synonyms && t.synonyms.length > 0 && (
            <div style={{ fontSize: 11, color: "var(--ios-text-tertiary)", marginTop: 6 }}>
              Synonyms: {t.synonyms.join(", ")}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: 6,
  border: "1px solid var(--ios-separator)",
  background: "transparent",
  color: "inherit",
  fontSize: 13,
  marginBottom: 8,
};
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