import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";
import { api } from "../../../services/api";
import { useWorkspaceStore } from "../../../store/workspaceStore";
import { useWizardStore } from "../../../store/wizardStore";
import ProgressBar from "../../../components/ProgressBar";

export default function Step5SchemaBuilder({ onNext, onBack }) {
  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const saveStep = useWizardStore((s) => s.saveStep);

  const [datasets, setDatasets] = useState([]);
  const [datasetId, setDatasetId] = useState("");
  const [ddl, setDdl] = useState("");
  const [columnsResolved, setColumnsResolved] = useState([]);
  const [tableName, setTableName] = useState("");
  const [generating, setGenerating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [progress, setProgress] = useState({
    percent: 0,
    message: "",
    visible: false,
  });

  useEffect(() => {
    (async () => {
      setLoadingDatasets(true);
      try {
        const list = await api.listDatasets(activeWorkspace.id);
        setDatasets(list || []);
        const candidate =
          list.find((d) => !d.schema_applied) || list[0] || null;
        if (candidate) setDatasetId(candidate.id);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingDatasets(false);
      }
    })();
  }, [activeWorkspace.id]);

  const handleGenerate = async () => {
    if (!datasetId) {
      setError("Please select a dataset first.");
      return;
    }
    setError(null);
    setResult(null);
    setGenerating(true);
    try {
      const res = await api.generateDDL(activeWorkspace.id, {
        dataset_id: datasetId,
      });
      setDdl(res.ddl);
      setColumnsResolved(res.columns_resolved);
      setTableName(res.table_name);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleApply = async () => {
    setError(null);
    setApplying(true);
    setProgress({ percent: 0, message: "Starting...", visible: true });

    const pollKey = `${activeWorkspace.id}:apply`;
    let stopped = false;

    const poll = async () => {
      while (!stopped) {
        try {
          const job = await api.getProgress(pollKey);
          if (job && job.status === "running") {
            setProgress({
              percent: job.percent || 0,
              message: job.message || "Processing...",
              visible: true,
            });
          }
        } catch {}
        await new Promise((r) => setTimeout(r, 800));
      }
    };
    poll();

    try {
      const res = await api.applySchema(activeWorkspace.id, {
        dataset_id: datasetId,
        ddl,
        columns_resolved: columnsResolved,
        table_name: tableName,
        drop_if_exists: true,
      });
      setResult(res);
      setProgress({ percent: 100, message: "Done", visible: true });
      setTimeout(() => setProgress((p) => ({ ...p, visible: false })), 1500);
    } catch (err) {
      setError(err.message);
      setProgress((p) => ({ ...p, visible: false }));
    } finally {
      stopped = true;
      setApplying(false);
    }
  };

  const handleContinue = async () => {
    if (!result) {
      setError("Apply schema first");
      return;
    }
    await saveStep(activeWorkspace.id, 5, {
      table_name: tableName,
      schema_id: result.schema_id,
      dataset_id: datasetId,
    });
    onNext();
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>Step 5 — Schema Builder</h2>
      <p style={{ color: "var(--ios-text-secondary)", marginBottom: 20, fontSize: 14 }}>
        Auto-generate DDL from your dataset, review, then apply.
      </p>

      <label style={{ display: "block", fontSize: 13, marginBottom: 6 }}>
        Dataset
      </label>
      <select
        value={datasetId}
        onChange={(e) => {
          setDatasetId(e.target.value);
          setDdl("");
          setResult(null);
        }}
        disabled={loadingDatasets}
        style={{
          width: "100%",
          padding: "8px 12px",
          borderRadius: 6,
          border: "1px solid #374151",
          background: "transparent",
          color: "inherit",
          fontSize: 13,
          marginBottom: 12,
        }}
      >
        {loadingDatasets && <option>Loading datasets...</option>}
        {!loadingDatasets && datasets.length === 0 && (
          <option value="">No datasets uploaded — go back to Step 4</option>
        )}
        {datasets.map((d) => (
          <option key={d.id} value={d.id}>
            {d.name} ({d.row_count} rows{d.schema_applied ? " — applied" : ""})
          </option>
        ))}
      </select>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button
          onClick={handleGenerate}
          disabled={generating || !datasetId}
          style={btnStyle("#6b7280")}
        >
          {generating ? "Generating..." : "Generate DDL"}
        </button>
        <button
          onClick={handleApply}
          disabled={applying || !ddl}
          style={btnStyle("#10b981")}
        >
          {applying ? "Applying..." : "Apply Schema"}
        </button>
      </div>

      <ProgressBar
        percent={progress.percent}
        message={progress.message}
        visible={progress.visible}
      />

      {error && (
        <div style={{ color: "#f87171", marginBottom: 12, fontSize: 13 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ color: "#10b981", marginBottom: 12, fontSize: 13 }}>
          Applied: <strong>{result.table_name}</strong> — {result.rows_inserted} rows inserted.
        </div>
      )}

      {ddl && (
        <div
          style={{
            border: "1px solid #374151",
            borderRadius: 8,
            overflow: "hidden",
            marginTop: 12,
          }}
        >
          <Editor
            height="320px"
            defaultLanguage="sql"
            value={ddl}
            onChange={(v) => setDdl(v || "")}
            theme="vs-dark"
            options={{ minimap: { enabled: false }, fontSize: 13 }}
          />
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <button onClick={onBack} style={btnStyle("#6b7280")}>Back</button>
        <button onClick={handleContinue} disabled={!result} style={btnStyle("#3b82f6")}>
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