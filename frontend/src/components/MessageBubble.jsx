import ReactMarkdownLite from "./MarkdownLite";

const styles = {
  row: (role) => ({
    display: "flex",
    justifyContent: role === "user" ? "flex-end" : "flex-start",
    marginBottom: "10px",
  }),
  bubble: (role) => ({
    maxWidth: "72%",
    padding: "10px 16px",
    borderRadius: "20px",
    background:
      role === "user" ? "var(--ios-blue)" : "var(--ios-gray-bubble)",
    color: role === "user" ? "#FFFFFF" : "var(--ios-text)",
    fontSize: "16px",
    lineHeight: "1.42",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.04)",
  }),
  bubbleUser: {
    borderBottomRightRadius: "6px",
  },
  bubbleAssistant: {
    borderBottomLeftRadius: "6px",
  },
  insight: {
    marginTop: "10px",
    paddingTop: "10px",
    borderTop:
      "1px solid rgba(255, 255, 255, 0.24)",
    fontSize: "14px",
    lineHeight: "1.5",
    opacity: 0.94,
  },
  insightOnLight: {
    borderTop: "1px solid rgba(0, 0, 0, 0.08)",
  },
};

export default function MessageBubble({ message }) {
  const content = (message.content || "").trim();
  const insight = (message.insight || "").trim();
  const showInsight = insight && insight !== content;
  const isUser = message.role === "user";

  return (
    <div style={styles.row(message.role)}>
      <div
        style={{
          ...styles.bubble(message.role),
          ...(isUser ? styles.bubbleUser : styles.bubbleAssistant),
        }}
      >
        <ReactMarkdownLite text={content} />
        {showInsight && (
          <div
            style={{
              ...styles.insight,
              ...(isUser ? {} : styles.insightOnLight),
            }}
          >
            <ReactMarkdownLite text={insight} />
          </div>
        )}
      </div>
    </div>
  );
}