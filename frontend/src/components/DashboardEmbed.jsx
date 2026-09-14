import { CloseIcon } from "./Icons";

const styles = {
  container: {
    background: "var(--ios-surface)",
    borderLeft: "1px solid var(--ios-separator)",
    display: "flex",
    flexDirection: "column",
    minWidth: "40%",
  },
  toolbar: {
    padding: "10px 14px",
    borderBottom: "1px solid var(--ios-separator)",
    background: "var(--ios-surface-2)",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  urlBar: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    gap: "8px",
    background: "var(--ios-surface)",
    border: "1px solid var(--ios-separator)",
    borderRadius: "10px",
    padding: "6px 12px",
    fontSize: "12px",
    color: "var(--ios-text-secondary)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  dot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "var(--ios-green)",
    flexShrink: 0,
  },
  urlText: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  actionBtn: {
    width: "32px",
    height: "32px",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "transparent",
    color: "var(--ios-text-secondary)",
  },
  iframe: {
    flex: 1,
    border: "none",
    background: "#FFFFFF",
  },
  empty: {
    padding: "40px 32px",
    color: "var(--ios-text-secondary)",
    fontSize: "14px",
    textAlign: "center",
    lineHeight: 1.55,
  },
  emptyTitle: {
    fontSize: "17px",
    fontWeight: "600",
    color: "var(--ios-text)",
    marginBottom: "6px",
    letterSpacing: "-0.01em",
  },
  emptyHint: {
    marginTop: "14px",
    padding: "10px 14px",
    background: "var(--ios-surface-2)",
    borderRadius: "var(--radius-sm)",
    display: "inline-block",
    fontStyle: "italic",
    fontSize: "13px",
  },
};

function shortenUrl(url) {
  if (!url) return "";
  try {
    const u = new URL(url);
    return u.pathname.length > 40 ? u.pathname.slice(0, 40) + "..." : u.pathname;
  } catch {
    return url.slice(0, 40);
  }
}

export default function DashboardEmbed({ url, onClose }) {
  if (!url) {
    return (
      <aside style={{ ...styles.container, width: "40%" }}>
        <div style={styles.toolbar}>
          <div style={styles.urlBar}>
            <div style={{ ...styles.dot, background: "var(--ios-text-tertiary)" }} />
            <span style={styles.urlText}>No dashboard loaded</span>
          </div>
          {onClose && (
            <button style={styles.actionBtn} onClick={onClose} aria-label="Close">
              <CloseIcon size={16} color="var(--ios-text-secondary)" />
            </button>
          )}
        </div>
        <div style={styles.empty}>
          <div style={styles.emptyTitle}>No dashboard yet</div>
          <div>
            Ask BIthere to build one, for example: build a fraud analytics
            dashboard with monthly trend and top 10 states.
          </div>
          <div style={styles.emptyHint}>
            "Buat dashboard fraud dengan monthly trend"
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside style={{ ...styles.container, width: "55%" }}>
      <div style={styles.toolbar}>
        <div style={styles.urlBar}>
          <div style={styles.dot} />
          <span style={styles.urlText}>{shortenUrl(url)}</span>
        </div>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="ios-btn-ghost"
          style={{
            padding: "6px 10px",
            fontSize: "13px",
            borderRadius: "8px",
          }}
        >
          Open
        </a>
        {onClose && (
          <button style={styles.actionBtn} onClick={onClose} aria-label="Close">
            <CloseIcon size={16} color="var(--ios-text-secondary)" />
          </button>
        )}
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