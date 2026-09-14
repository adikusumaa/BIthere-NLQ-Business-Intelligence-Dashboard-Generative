const styles = {
  container: {
    borderLeft: "1px solid var(--color-border)",
    background: "var(--color-bg-soft)",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    padding: "10px 16px",
    borderBottom: "1px solid var(--color-border)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "13px",
    fontWeight: "600",
    color: "var(--color-text-dim)",
  },
  link: {
    fontSize: "12px",
    color: "var(--color-accent)",
  },
  iframe: {
    flex: 1,
    border: "none",
    background: "#ffffff",
  },
  empty: {
    padding: "24px",
    color: "var(--color-text-dim)",
    fontSize: "13px",
    textAlign: "center",
  },
};

export default function DashboardEmbed({ url, onClose }) {
  if (!url) {
    return (
      <aside style={{ ...styles.container, width: "40%" }}>
        <div style={styles.header}>Dashboard</div>
        <div style={styles.empty}>
          Dashboard belum dibuat.
          <br />
          Minta lewat chat, contoh:
          <br />
          <em>"Tampilkan dashboard fraud per brand"</em>
        </div>
      </aside>
    );
  }

  return (
    <aside style={{ ...styles.container, width: "55%" }}>
      <div style={styles.header}>
        <span>Dashboard</span>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            style={styles.link}
          >
            Buka di tab baru
          </a>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                color: "var(--color-text-dim)",
                fontSize: "16px",
                lineHeight: "1",
              }}
              aria-label="Tutup dashboard"
            >
              ×
            </button>
          )}
        </div>
      </div>
      <iframe
        style={styles.iframe}
        src={url}
        title="BIthere Dashboard"
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
      />
    </aside>
  );
}