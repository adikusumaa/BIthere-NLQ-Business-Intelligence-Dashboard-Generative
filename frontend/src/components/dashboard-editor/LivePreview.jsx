import { useRef, useState } from "react";
import { api } from "../../services/api";

const CELL_W = 40;
const CELL_H = 30;
const GRID_COLS = 24;

export default function LivePreview({
  workspaceId,
  dashboardId,
  state,
  selectedCardId,
  onSelectCard,
  sessionId,
  onApplied,
}) {
  const [dragging, setDragging] = useState(null); // { cardId, offsetX, offsetY, origRow, origCol }
  const [previewPos, setPreviewPos] = useState(null); // { row, col }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const gridRef = useRef(null);

  if (!state || !state.pages || state.pages.length === 0) {
    return (
      <div style={{ padding: 16, color: "var(--ios-text-secondary)", fontSize: 12 }}>
        Empty dashboard.
      </div>
    );
  }

  const page = state.pages[0];

  const handleMouseDown = (e, card) => {
    if (busy) return;
    e.preventDefault();
    const rect = gridRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const cardLeft = card.position.col * CELL_W;
    const cardTop = card.position.row * CELL_H;

    setDragging({
      cardId: card.id,
      offsetX: mouseX - cardLeft,
      offsetY: mouseY - cardTop,
      origRow: card.position.row,
      origCol: card.position.col,
      size_x: card.position.size_x,
      size_y: card.position.size_y,
    });
    setPreviewPos({ row: card.position.row, col: card.position.col });
    onSelectCard?.(card.id);
  };

  const handleMouseMove = (e) => {
    if (!dragging) return;
    const rect = gridRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let newCol = Math.round((mouseX - dragging.offsetX) / CELL_W);
    let newRow = Math.round((mouseY - dragging.offsetY) / CELL_H);

    newCol = Math.max(0, Math.min(GRID_COLS - dragging.size_x, newCol));
    newRow = Math.max(0, newRow);

    setPreviewPos({ row: newRow, col: newCol });
  };

  const handleMouseUp = async () => {
    if (!dragging || !previewPos) {
      setDragging(null);
      return;
    }

    const changed =
      previewPos.row !== dragging.origRow || previewPos.col !== dragging.origCol;

    const dragData = { ...dragging };
    setDragging(null);
    setPreviewPos(null);

    if (!changed) return;

    setBusy(true);
    setError(null);
    try {
      const patch = {
        patch_type: "MOVE_CARD",
        card_id: dragData.cardId,
        new_position: {
          row: previewPos.row,
          col: previewPos.col,
          size_x: dragData.size_x,
          size_y: dragData.size_y,
        },
      };

      const res = await api.manualEditDashboard(workspaceId, dashboardId, {
        patch,
        base_version: state.version,
        session_id: sessionId,
      });

      if (onApplied) onApplied(res.state);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <div style={{ marginBottom: 12 }}>
        <strong style={{ fontSize: 14 }}>{page.name}</strong>
        <span style={{ fontSize: 11, color: "var(--ios-text-secondary)", marginLeft: 8 }}>
          v{state.version} · {page.cards.length} cards
        </span>
        {busy && (
          <span style={{ marginLeft: 8, fontSize: 11, color: "var(--ios-blue)" }}>saving...</span>
        )}
        {error && (
          <span style={{ marginLeft: 8, fontSize: 11, color: "#f87171" }}>{error}</span>
        )}
      </div>

      <div
        ref={gridRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          position: "relative",
          width: GRID_COLS * CELL_W,
          minHeight: 600,
          backgroundImage:
            "linear-gradient(to right, rgba(128,128,128,0.08) 1px, transparent 1px), " +
            "linear-gradient(to bottom, rgba(128,128,128,0.08) 1px, transparent 1px)",
          backgroundSize: `${CELL_W}px ${CELL_H}px`,
          borderRadius: 8,
          border: "1px dashed var(--ios-separator)",
          userSelect: "none",
        }}
      >
        {page.cards.map((card) => {
          const isSelected = card.id === selectedCardId;
          const isDragging = dragging?.cardId === card.id;
          const pos = isDragging && previewPos ? previewPos : card.position;
          const color = card.style?.color || "#3b82f6";

          return (
            <div
              key={card.id}
              onMouseDown={(e) => handleMouseDown(e, card)}
              onClick={() => onSelectCard?.(card.id)}
              style={{
                position: "absolute",
                left: pos.col * CELL_W,
                top: pos.row * CELL_H,
                width: card.position.size_x * CELL_W - 4,
                height: card.position.size_y * CELL_H - 4,
                padding: 8,
                background: "var(--ios-surface)",
                border: isSelected
                  ? "2px solid #3b82f6"
                  : isDragging
                  ? "2px dashed #3b82f6"
                  : "1px solid var(--ios-separator)",
                borderRadius: 8,
                cursor: isDragging ? "grabbing" : "grab",
                overflow: "hidden",
                boxShadow: isSelected ? "0 0 0 3px rgba(59,130,246,0.2)" : "none",
                opacity: isDragging ? 0.7 : 1,
                transition: isDragging ? "none" : "left 0.15s ease, top 0.15s ease",
                zIndex: isDragging ? 10 : 1,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {card.title}
                </div>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
              </div>

              <div style={{ fontSize: 9, color: "var(--ios-text-tertiary)", textTransform: "uppercase" }}>
                {card.type}
              </div>

              {card.sql && (
                <div
                  style={{
                    fontSize: 9,
                    color: "var(--ios-text-tertiary)",
                    marginTop: 4,
                    fontFamily: "monospace",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {card.sql.slice(0, 60)}...
                </div>
              )}

              {isDragging && previewPos && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 4,
                    right: 6,
                    fontSize: 9,
                    color: "#3b82f6",
                    fontWeight: 600,
                  }}
                >
                  r{previewPos.row} c{previewPos.col}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {page.filters && page.filters.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Filters</div>
          {page.filters.map((f) => (
            <div key={f.id} style={{ fontSize: 11, color: "var(--ios-text-secondary)", padding: "3px 0" }}>
              · {f.name} ({f.type}) on {f.column}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}