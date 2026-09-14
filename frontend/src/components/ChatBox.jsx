import { useRef, useState } from "react";

import { SendIcon } from "./Icons";

const styles = {
  container: {
    padding: "12px 20px 20px 20px",
    background: "var(--ios-bg)",
    borderTop: "1px solid var(--ios-separator)",
  },
  row: {
    display: "flex",
    alignItems: "flex-end",
    gap: "10px",
    background: "var(--ios-surface)",
    border: "1px solid var(--ios-separator)",
    borderRadius: "22px",
    padding: "6px 6px 6px 18px",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
  },
  rowFocused: {
    borderColor: "var(--ios-blue)",
    boxShadow: "0 0 0 4px var(--ios-blue-tint)",
  },
  textarea: {
    flex: 1,
    minHeight: "24px",
    maxHeight: "160px",
    padding: "8px 0",
    background: "transparent",
    border: "none",
    color: "var(--ios-text)",
    fontSize: "16px",
    resize: "none",
    lineHeight: "1.42",
    fontFamily: "inherit",
  },
  sendBtn: (active) => ({
    width: "34px",
    height: "34px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: active ? "var(--ios-blue)" : "var(--ios-text-tertiary)",
    transition: "background 0.15s ease, transform 0.1s ease",
    flexShrink: 0,
  }),
  hint: {
    fontSize: "11px",
    color: "var(--ios-text-tertiary)",
    marginTop: "8px",
    textAlign: "center",
  },
};

export default function ChatBox({ onSend, disabled }) {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef(null);

  const handleSubmit = (event) => {
    if (event) event.preventDefault();
    if (disabled) return;
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  const handleInput = (event) => {
    setValue(event.target.value);
    const el = event.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  };

  const active = Boolean(value.trim()) && !disabled;

  return (
    <form style={styles.container} onSubmit={handleSubmit}>
      <div
        style={{
          ...styles.row,
          ...(focused ? styles.rowFocused : {}),
        }}
      >
        <textarea
          ref={textareaRef}
          style={styles.textarea}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={
            disabled ? "Processing..." : "Ask anything about the data..."
          }
          disabled={disabled}
          rows={1}
        />
        <button
          type="submit"
          style={styles.sendBtn(active)}
          disabled={!active}
          aria-label="Send"
        >
          <SendIcon size={16} color="#FFFFFF" />
        </button>
      </div>
      <div style={styles.hint}>
        Press Enter to send, Shift + Enter for new line
      </div>
    </form>
  );
}