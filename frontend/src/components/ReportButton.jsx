import { useEffect, useRef, useState } from "react";

import { FileIcon, MailIcon, MenuIcon } from "./Icons";
import { useAuthStore } from "../store/authStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const styles = {
  wrapper: { position: "relative" },
  trigger: (active, disabled) => ({
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: active ? "var(--ios-blue-tint)" : "var(--ios-surface-2)",
    opacity: disabled ? 0.4 : 1,
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "background 0.15s ease",
  }),
  menu: {
    position: "absolute",
    top: "calc(100% + 8px)",
    right: 0,
    minWidth: "240px",
    background: "var(--ios-surface)",
    border: "1px solid var(--ios-separator)",
    borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-lg)",
    zIndex: 200,
    overflow: "hidden",
    animation: "menuFadeIn 0.15s ease",
  },
  item: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "12px 16px",
    fontSize: "15px",
    textAlign: "left",
    color: "var(--ios-text)",
    background: "var(--ios-surface)",
    borderBottom: "1px solid var(--ios-separator)",
  },
  itemLast: {
    borderBottom: "none",
  },
  status: (ok) => ({
    padding: "10px 16px",
    fontSize: "13px",
    color: ok ? "var(--ios-green)" : "var(--ios-red)",
    background: ok
      ? "rgba(52, 199, 89, 0.08)"
      : "rgba(255, 59, 48, 0.08)",
    textAlign: "center",
  }),
};

const FALLBACK_INSIGHT =
  "Dashboard telah dibuat. Buka dashboard di panel kanan " +
  "untuk mengeksplorasi visualisasi interaktif, atau kirim laporan ini " +
  "ke email untuk mendapatkan ringkasan lengkap beserta tangkapan layar.";

export default function ReportButton({ insight, dashboardUrl }) {
  const getToken = useAuthStore((s) => s.getToken);
  const userEmail = useAuthStore((s) => s.user?.email);

  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null);
  const wrapRef = useRef(null);

  const hasContent = Boolean(insight) || Boolean(dashboardUrl);
  const disabled = !hasContent;

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapRef.current && !wrapRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const send = async (channel) => {
    if (!hasContent) return;
    setBusy(true);
    setStatus(null);
    try {
      const body = {
        title: "BIthere Report",
        insight: insight || FALLBACK_INSIGHT,
        dashboard_url: dashboardUrl || null,
        channels: [channel],
      };
      if (channel === "email") {
        body.email_recipient = userEmail;
        body.email_subject = "[BIthere] Report";
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
      setStatus({ ok: true, msg: `${channel.toUpperCase()} sent` });
      setTimeout(() => {
        setStatus(null);
        setOpen(false);
      }, 2200);
    } catch (err) {
      setStatus({ ok: false, msg: err.message});
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={styles.wrapper} ref={wrapRef}>
      <button
        style={styles.trigger(open, disabled)}
        onClick={() => !disabled && setOpen((v) => !v)}
        disabled={disabled || busy}
        title={
          disabled
            ? "No insight or dashboard to send yet"
            : "Send report"
        }
        aria-label="Send report"
      >
        <MenuIcon size={18} color={disabled ?"var(--ios-text-tertiary)" : "var(--ios-blue)"} />
      </button>

      {open && !busy && (
        <div style={styles.menu}>
          <button
            style={styles.item}
            onClick={() => send("pdf")}
          >
            <FileIcon size={18} color="var(--ios-blue)" />
            <span>Export PDF</span>
          </button>
          <button
            style={styles.item}
            onClick={() => send("email")}
          >
            <MailIcon size={18} color="var(--ios-blue)" />
            <span>Send to Email</span>
          </button>
          <button
            style={{ ...styles.item, ...styles.itemLast }}
            onClick={() => send("slack")}
          >
            <MailIcon size={18} color="var(--ios-blue)" />
            <span>Send to Slack</span>
          </button>
          {status && (
            <div style={styles.status(status.ok)}>{status.msg}</div>
          )}
        </div>
      )}
    </div>
  );
}