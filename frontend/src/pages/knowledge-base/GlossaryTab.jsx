import { useEffect, useRef, useState } from "react";
import ConfirmDialog from "../../components/ConfirmDialog";
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
  const [confirmId, setConfirmId] = useState(null);
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

  const handleDelete = (id) => {
    setConfirmId(id);
  };

  const confirmDeleteNow = async () => {
    const id = confirmId;
    setConfirmId(null);
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
      <div
        style={{
          background: "var(--ios-surface)",
          borderRadius: "var(--radius-md)",
          padding: "18px 20px",
          marginBottom: 20,
          border: "1px solid var(--ios-separator)",
          boxShadow: "var(--shadow-xs)",
        }}
      >
        <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 14, color: "var(--ios-text)" }}>
          Add term
        </div>

        <input
          placeholder="Term (e.g. chargeback)"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          className="ios-input"
          style={{ width: "100%", marginBottom: 10 }}
        />
        <textarea
          placeholder="Definition..."
          value={definition}
          onChange={(e) => setDefinition(e.target.value)}
          rows={3}
          className="ios-input"
          style={{ width: "100%", resize: "vertical", marginBottom: 12, fontFamily: "inherit" }}
        />

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            onClick={handleAdd}
            disabled={adding || !term || !definition}
            className="ios-btn ios-btn-pill"
            style={{
              padding: "9px 20px",
              fontSize: 14,
              fontWeight: 600,
              background: "var(--ios-green)",
              color: "#FFFFFF",
            }}
          >
            {adding ? "Adding..." : "Add Term"}
          </button>
          <button
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="ios-btn ios-btn-pill"
            style={{
              padding: "9px 20px",
              fontSize: 14,
              fontWeight: 600,
              background: "var(--ios-surface-2)",
              color: "var(--ios-text)",
            }}
          >
            {uploading ? "Uploading..." : "Upload CSV"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={(e) => e.target.files?.[0] && handleCsv(e.target.files[0])}
          />
        </div>

        <div style={{ fontSize: 12, color: "var(--ios-text-tertiary)", marginTop: 10 }}>
          CSV columns: term, definition, category, synonyms (pipe-separated)
        </div>
      </div>

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

      {loading && <div style={{ color: "var(--ios-text-secondary)", fontSize: 14 }}>Loading...</div>}
      {!loading && terms.length === 0 && (
        <div style={{ color: "var(--ios-text-secondary)", fontSize: 15 }}>No terms yet.</div>
      )}

      {terms.map((t) => (
        <div
          key={t.id}
          style={{
            background: "var(--ios-surface)",
            borderRadius: "var(--radius-md)",
            padding: "14px 18px",
            marginBottom: 10,
            border: "1px solid var(--ios-separator)",
            boxShadow: "var(--shadow-xs)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 6,
              gap: 12,
            }}
          >
            <span style={{ fontSize: 16, fontWeight: 700, color: "var(--ios-text)" }}>
              {t.term}
            </span>
            <button
              onClick={() => handleDelete(t.id)}
              className="ios-btn ios-btn-pill"
              style={{
                padding: "5px 14px",
                fontSize: 13,
                fontWeight: 600,
                background: "var(--ios-red)",
                color: "#FFFFFF",
              }}
            >
              Delete
            </button>
          </div>
          <div style={{ fontSize: 14, color: "var(--ios-text-secondary)", lineHeight: 1.5 }}>
            {t.definition}
          </div>
          {t.synonyms && t.synonyms.length > 0 && (
            <div style={{ fontSize: 12, color: "var(--ios-text-tertiary)", marginTop: 8 }}>
              Synonyms: {t.synonyms.join(", ")}
            </div>
          )}
        </div>
      ))}

      <ConfirmDialog
        open={!!confirmId}
        title="Delete term?"
        message="This glossary term will be removed from the knowledge base. It will not be searchable anymore until re-added."
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={confirmDeleteNow}
        onCancel={() => setConfirmId(null)}
      />
    </div>
  );
}