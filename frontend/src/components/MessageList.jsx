import { useEffect, useRef } from "react";

import MessageBubble from "./MessageBubble";

const styles = {
  container: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 20px 8px 20px",
  },
  empty: {
    color: "var(--ios-text-secondary)",
    textAlign: "center",
    padding: "60px 20px",
    fontSize: "15px",
    lineHeight: 1.5,
    maxWidth: "380px",
    margin: "0 auto",
  },
  emptyTitle: {
    fontSize: "22px",
    fontWeight: "600",
    color: "var(--ios-text)",
    marginBottom: "8px",
    letterSpacing: "-0.02em",
  },
  emptyHint: {
    fontSize: "14px",
    color: "var(--ios-text-secondary)",
    marginTop: "16px",
    padding: "12px 16px",
    background: "var(--ios-surface)",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--ios-separator)",
    display: "inline-block",
    fontStyle: "italic",
  },
};

export default function MessageList({ messages, isStreaming }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  if (!messages.length) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>
          <div style={styles.emptyTitle}>BIthere</div>
          <div>Ask anything about the fraud dataset.</div>
          <div style={styles.emptyHint}>
            "Berapa total transaksi fraud di bulan Januari 2010?"
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {messages.map((msg, idx) => (
        <MessageBubble key={idx} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}