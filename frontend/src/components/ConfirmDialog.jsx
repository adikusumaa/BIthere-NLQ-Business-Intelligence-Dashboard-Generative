import { useEffect } from "react";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  variant = "danger",
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    if (!open) return;
    const onEsc = (e) => {
      if (e.key === "Escape") onCancel?.();
    };
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [open, onCancel]);

  if (!open) return null;

  const confirmColor = variant === "danger" ? "var(--ios-red)" : "var(--ios-blue)";

  return (
    <div
      onClick={onCancel}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.45)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 3000,
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%",
          maxWidth: 400,
          background: "var(--ios-surface)",
          borderRadius: 20,
          padding: "28px 24px 20px",
          boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: "var(--ios-text)" }}>
          {title}
        </div>
        {message && (
          <div
            style={{
              fontSize: 14,
              color: "var(--ios-text-secondary)",
              lineHeight: 1.5,
              marginBottom: 22,
              whiteSpace: "pre-line",
            }}
          >
            {message}
          </div>
        )}
        <div style={{ display: "flex", gap: 10 }}>
          <button
            onClick={onCancel}
            className="ios-btn-secondary"
            style={{
              flex: 1,
              padding: "12px",
              borderRadius: 12,
              fontSize: 15,
              fontWeight: 600,
              background: "var(--ios-surface-2)",
              color: "var(--ios-text)",
              border: "none",
              cursor: "pointer",
            }}
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            style={{
              flex: 1,
              padding: "12px",
              borderRadius: 12,
              fontSize: 15,
              fontWeight: 600,
              background: confirmColor,
              color: "#FFFFFF",
              border: "none",
              cursor: "pointer",
            }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}