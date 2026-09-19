import { useEffect, useState } from "react";
import { api } from "../../services/api";

const CHART_TYPES = ["scalar", "bar", "line", "pie", "area", "table", "text"];

export default function PropertyPanel({
  workspaceId,
  dashboardId,
  state,
  selectedCardId,
  sessionId,
  onApplied,
}) {
  const [color, setColor] = useState("#3b82f6");
  const [title, setTitle] = useState("");
  const [chartType, setChartType] = useState("bar");
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState(null);

  const card = selectedCardId
    ? state?.pages?.flatMap((p) => p.cards).find((c) => c.id === selectedCardId)
    : null;

  useEffect(() => {
    if (card) {
      setColor(card.style?.color || "#3b82f6");
      setTitle(card.title);
      setChartType(card.type);
    }
  }, [selectedCardId, card?.id, state?.version]);

  const sendPatch = async (patch) => {
    setError(null);
    setApplying(true);
    try {
      const res = await api.manualEditDashboard(workspaceId, dashboardId, {
        patch,
        base_version: state.version,
        session_id: sessionId,
      });
      if (onApplied) onApplied(res.state);
    } catch (err) {
      setError(err.message);
    } finally {
      setApplying(false);
    }
  };

  if (!card) {
    return (
      <div style={{ padding: 12, fontSize: 12, color: "var(--ios-text-tertiary)" }}>
        Click a card in the preview to edit its properties.
      </div>
    );
  }

  return (
    <div style={{ padding: 12 }}>
      <strong style={{ fontSize: 13, display: "block", marginBottom: 10 }}>Properties</strong>
      <div style={{ fontSize: 10, color: "var(--ios-text-tertiary)", marginBottom: 10 }}>
        card: {card.id}
      </div>

      {error && <div style={{ color: "#f87171", fontSize: 11, marginBottom: 8 }}>{error}</div>}

      <label style={label}>Title</label>
      <div style={{ display: "flex", gap: 6 }}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={input}
        />
        <button
          onClick={() => sendPatch({ patch_type: "CHANGE_TITLE", card_id: card.id, new_title: title })}
          disabled={applying || title === card.title || !title.trim()}
          style={miniBtn}
        >
          ✓
        </button>
      </div>

      <label style={label}>Color</label>
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <input
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          style={{ width: 40, height: 30, border: "none", background: "transparent", cursor: "pointer" }}
        />
        <input
          value={color}
          onChange={(e) => setColor(e.target.value)}
          style={{ ...input, flex: 1 }}
        />
        <button
          onClick={() => sendPatch({ patch_type: "CHANGE_COLOR", card_id: card.id, color })}
          disabled={applying || color === card.style?.color}
          style={miniBtn}
        >
          ✓
        </button>
      </div>

      <label style={label}>Chart type</label>
      <div style={{ display: "flex", gap: 6 }}>
        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
          style={{ ...input, flex: 1 }}
        >
          {CHART_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <button
          onClick={() => sendPatch({ patch_type: "CHANGE_CHART_TYPE", card_id: card.id, new_type: chartType })}
          disabled={applying || chartType === card.type}
          style={miniBtn}
        >
          ✓
        </button>
      </div>

      <div style={{ marginTop: 16, fontSize: 10, color: "var(--ios-text-tertiary)" }}>
        Position: r{card.position.row} c{card.position.col} ({card.position.size_x}×{card.position.size_y})
      </div>
    </div>
  );
}

const label = { display: "block", fontSize: 11, color: "var(--ios-text-secondary)", marginTop: 12, marginBottom: 4 };
const input = {
  padding: "6px 8px",
  borderRadius: 4,
  border: "1px solid var(--ios-separator)",
  background: "transparent",
  color: "inherit",
  fontSize: 12,
  width: "100%",
};
const miniBtn = {
  padding: "0 10px",
  borderRadius: 4,
  border: "none",
  background: "#10b981",
  color: "white",
  fontSize: 12,
  cursor: "pointer",
  minWidth: 32,
};