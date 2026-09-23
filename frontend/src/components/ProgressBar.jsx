export default function ProgressBar({ percent = 0, message = "", visible = false }) {
  if (!visible) return null;

  const pct = Math.max(0, Math.min(100, percent));

  return (
    <div style={{ marginTop: 12, marginBottom: 12 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          color: "var(--ios-text-secondary)",
          marginBottom: 6,
        }}
      >
        <span>{message || "Processing..."}</span>
        <span>{pct}%</span>
      </div>
      <div
        style={{
          width: "100%",
          height: 6,
          background: "var(--ios-surface-2)",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: "var(--ios-blue)",
            borderRadius: 3,
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}