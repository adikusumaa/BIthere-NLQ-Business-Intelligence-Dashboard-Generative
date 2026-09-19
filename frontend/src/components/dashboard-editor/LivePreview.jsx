export default function LivePreview({ state, selectedCardId, onSelectCard }) {
  if (!state || !state.pages || state.pages.length === 0) {
    return <div style={{ padding: 16, color: "var(--ios-text-secondary)", fontSize: 12 }}>Empty dashboard.</div>;
  }

  const page = state.pages[0];

  const cellWidth = 40;  // px per grid column (approx)
  const cellHeight = 30; // px per grid row

  return (
    <div style={{ padding: 16 }}>
      <div style={{ marginBottom: 12 }}>
        <strong style={{ fontSize: 14 }}>{page.name}</strong>
        <span style={{ fontSize: 11, color: "var(--ios-text-secondary)", marginLeft: 8 }}>
          v{state.version} · {page.cards.length} cards
        </span>
      </div>

      <div
        style={{
          position: "relative",
          width: 24 * cellWidth,
          minHeight: 600,
          background: "rgba(0,0,0,0.15)",
          borderRadius: 8,
          border: "1px dashed var(--ios-separator)",
        }}
      >
        {page.cards.map((card) => {
          const isSelected = card.id === selectedCardId;
          const pos = card.position;
          const color = card.style?.color || "#3b82f6";

          return (
            <div
              key={card.id}
              onClick={() => onSelectCard?.(card.id)}
              style={{
                position: "absolute",
                left: pos.col * cellWidth,
                top: pos.row * cellHeight,
                width: pos.size_x * cellWidth - 4,
                height: pos.size_y * cellHeight - 4,
                padding: 8,
                background: "var(--ios-surface)",
                border: isSelected ? "2px solid #3b82f6" : "1px solid var(--ios-separator)",
                borderRadius: 8,
                cursor: "pointer",
                overflow: "hidden",
                boxShadow: isSelected ? "0 0 0 3px rgba(59,130,246,0.2)" : "none",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <div style={{ fontSize: 11, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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