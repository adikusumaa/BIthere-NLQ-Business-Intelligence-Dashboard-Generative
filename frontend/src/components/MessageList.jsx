import { useEffect, useRef } from "react";

import MessageBubble from "./MessageBubble";

const styles = {
  container: {
    flex: 1,
    overflowY: "auto",
    padding: "20px",
  },
  empty: {
    color: "var(--color-text-dim)",
    textAlign: "center",
    padding: "40px 20px",
    fontSize: "13px",
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
          Mulai percakapan dengan bertanya tentang data fraud,
          <br />
          misalnya: <em>"Berapa total transaksi fraud di bulan Januari 2010?"</em>
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