import ReactMarkdownLite from "./MarkdownLite";

const styles = {
  row: (role) => ({
    display: "flex",
    justifyContent: role === "user" ? "flex-end" : "flex-start",
    marginBottom: "12px",
  }),
  bubble: (role) => ({
    maxWidth: "75%",
    padding: "10px 14px",
    borderRadius: "10px",
    background:
      role === "user" ? "var(--color-accent)" : "var(--color-bg-soft)",
    color: role === "user" ? "#ffffff" : "var(--color-text)",
    border:
      role === "user" ? "none" : "1px solid var(--color-border)",
    fontSize: "14px",
    lineHeight: "1.6",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  }),
  insight: {
    marginTop: "8px",
    paddingTop: "8px",
    borderTop: "1px dashed var(--color-border)",
    fontSize: "13px",
    color: "var(--color-text-dim)",
  },
};

export default function MessageBubble({ message }) {
  const content = (message.content || "").trim();
  const insight = (message.insight || "").trim();
  const showInsight = insight && insight !== content;

  return (
    <div style={styles.row(message.role)}>
      <div style={styles.bubble(message.role)}>
        <ReactMarkdownLite text={content} />
        {showInsight && (
          <div style={styles.insight}>
            <ReactMarkdownLite text={`Insight: ${insight}`} />
          </div>
        )}
      </div>
    </div>
  );
}