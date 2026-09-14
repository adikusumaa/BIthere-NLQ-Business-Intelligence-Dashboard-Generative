import { useState } from "react";

import { useAuthStore } from "../store/authStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const styles = {
  wrapper: { position: "relative" },
  button: (active) => ({
    padding: "6px 12px",
    background: active ? "var(--color-accent)" : "transparent",
    color: active ? "#ffffff" : "var(--color-text-dim)",
    border: active
      ? "1px solid var(--color-accent)"
      : "1px solid var(--color-border)",
    borderRadius: "6px",
    fontSize: "12px",
    cursor: "pointer",
  }),
  buttonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  menu: {
    position: "absolute",
    top: "calc(100% + 6px)",
    right: 0,
    minWidth: "220px",
    background: "var(--color-bg-soft)",
    border: "1px solid var(--color-border)",
    borderRadius: "6px",
    boxShadow: "0 6px 20px rgba(0, 0, 0, 0.4)",
    zIndex: 100,
    overflow: "hidden",
  },
  item: {
    display: "block",
    width: "100%",
    padding: "10px 14px",
    background: "transparent",
    color: "var(--color-text)",
    textAlign: "left",
    fontSize: "13px",
    borderBottom: "1px solid var(--color-border)",
    cursor: "pointer",
  },
  message: {
    padding: "10px 14px",
    fontSize: "12px",
    color: "var(--color-text-dim)",
    background: "var(--color-bg)",
  },
};

const FALLBACK_INSIGHT =
  "Dashboard Fraud Analytics telah dibuat. Silakan buka dashboard " +
  "interaktif pada panel kanan untuk mengeksplorasi visualisasi lengkap " +
  "per halaman, termasuk KPI utama, tren bulanan, distribusi per brand, " +
  "dan breakdown per merchant.";

export default function ReportButton({ insight, dashboardUrl }) {
  const getToken = useAuthStore((s) => s.getToken);
  const userEmail = useAuthStore((s) => s.user?.email);

  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null);

  const hasContent = Boolean(insight) || Boolean(dashboardUrl);
  const disabled = !hasContent;

  const send = async (channel) => {
    if (!hasContent) return;
    setBusy(true);
    setStatus(null);
    try {
      const body = {
        title: "BIthere Fraud Report",
        insight: insight || FALLBACK_INSIGHT,
        dashboard_url: dashboardUrl || null,
        channels: [channel],
      };
      if (channel === "email") {
        body.email_recipient = userEmail;
        body.email_subject = "[BIthere] Fraud Report";
      }
      const response = await fetch(`${API_BASE_URL}/api/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setStatus({ ok: true, msg: `${channel.toUpperCase()} terkirim` });
      setTimeout(() => {
        setStatus(null);
        setOpen(false);
      }, 2200);
    } catch (err) {
      setStatus({ ok: false, msg: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={styles.wrapper}>
      <button
        style={{
          ...styles.button(open),
          ...(disabled ? styles.buttonDisabled : {}),
        }}
        onClick={() => setOpen((v) => !v)}
        disabled={disabled || busy}
        title={
          disabled
            ? "Belum ada insight atau dashboard untuk dikirim"
            : "Kirim laporan"
        }
      >
        {busy ? "..." : "Kirim Laporan"}
      </button>

      {open && !busy && (
        <div style={styles.menu}>
          <button style={styles.item} onClick={() => send("pdf")}>
            Export PDF
          </button>
          <button style={styles.item} onClick={() => send("email")}>
            Kirim ke Email ({userEmail})
          </button>
          <button
            style={{ ...styles.item, borderBottom: "none" }}
            onClick={() => send("slack")}
          >
            Kirim ke Slack
          </button>
          {status && (
            <div
              style={{
                ...styles.message,
                color: status.ok
                  ? "var(--color-success)"
                  : "var(--color-danger)",
              }}
            >
              {status.msg}
            </div>
          )}
        </div>
      )}
    </div>
  );
}