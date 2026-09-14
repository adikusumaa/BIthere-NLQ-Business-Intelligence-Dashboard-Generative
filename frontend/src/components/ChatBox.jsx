import { useState } from "react";

const styles = {
  container: {
    borderTop: "1px solid var(--color-border)",
    padding: "16px 20px",
    background: "var(--color-bg-soft)",
  },
  row: {
    display: "flex",
    gap: "10px",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    minHeight: "44px",
    maxHeight: "160px",
    padding: "11px 14px",
    background: "var(--color-bg)",
    border: "1px solid var(--color-border)",
    borderRadius: "8px",
    color: "var(--color-text)",
    fontSize: "14px",
    resize: "none",
    lineHeight: "1.5",
  },
  button: {
    padding: "11px 22px",
    background: "var(--color-accent)",
    color: "#ffffff",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: "600",
    transition: "background 0.15s",
  },
  hint: {
    fontSize: "11px",
    color: "var(--color-text-dim)",
    marginTop: "8px",
  },
};

export default function ChatBox({ onSend, disabled }) {
  const [value, setValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (disabled) return;
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  return (
    <form style={styles.container} onSubmit={handleSubmit}>
      <div style={styles.row}>
        <textarea
          style={styles.textarea}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            disabled ? "Sedang memproses..." : "Tanya apa saja tentang data..."
          }
          disabled={disabled}
        />
        <button type="submit" style={styles.button} disabled={disabled}>
          {disabled ? "..." : "Send"}
        </button>
      </div>
      <div style={styles.hint}>
        Enter untuk kirim, Shift+Enter untuk baris baru
      </div>
    </form>
  );
}