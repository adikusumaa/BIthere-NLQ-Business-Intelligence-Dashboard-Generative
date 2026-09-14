import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import ChatBox from "../components/ChatBox";
import DashboardEmbed from "../components/DashboardEmbed";
import MessageList from "../components/MessageList";
import ReportButton from "../components/ReportButton";
import { useAuthStore } from "../store/authStore";
import { useChatStore } from "../store/chatStore";

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: "var(--color-bg)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 20px",
    borderBottom: "1px solid var(--color-border)",
    background: "var(--color-bg-soft)",
  },
  brand: { display: "flex", alignItems: "center", gap: "10px" },
  brandName: {
    fontSize: "16px",
    fontWeight: "700",
    color: "var(--color-text)",
  },
  brandTag: { fontSize: "11px", color: "var(--color-text-dim)" },
  actions: { display: "flex", gap: "12px", alignItems: "center" },
  userEmail: { fontSize: "12px", color: "var(--color-text-dim)" },
  btn: {
    padding: "6px 12px",
    background: "transparent",
    color: "var(--color-text-dim)",
    border: "1px solid var(--color-border)",
    borderRadius: "6px",
    fontSize: "12px",
    textDecoration: "none",
  },
  body: { flex: 1, display: "flex", overflow: "hidden" },
  chatPane: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
  },
  errorBar: {
    padding: "8px 16px",
    background: "rgba(248, 81, 73, 0.1)",
    color: "var(--color-danger)",
    borderTop: "1px solid var(--color-danger)",
    fontSize: "12px",
  },
};

export default function Chat() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);
  const logout = useAuthStore((s) => s.logout);

  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);
  const activeDashboardUrl = useChatStore((s) => s.activeDashboardUrl);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const reset = useChatStore((s) => s.reset);

  const [showDashboard, setShowDashboard] = useState(true);

  const lastInsight = (() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].role === "assistant" && messages[i].insight) {
        return messages[i].insight;
      }
    }
    return null;
  })();

  const handleLogout = async () => {
    await logout();
    reset();
    navigate("/login");
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.brand}>
          <div style={styles.brandName}>BIthere</div>
          <div style={styles.brandTag}>AI Business Intelligence Analyst</div>
        </div>
        <div style={styles.actions}>
          <span style={styles.userEmail}>{user?.email}</span>
          <ReportButton
            insight={lastInsight}
            dashboardUrl={activeDashboardUrl}
          />
          {role === "admin" && (
            <Link to="/admin" style={styles.btn}>
              Admin
            </Link>
          )}
          <button
            style={styles.btn}
            onClick={() => setShowDashboard((v) => !v)}
          >
            {showDashboard ? "Sembunyikan dashboard" : "Tampilkan dashboard"}
          </button>
          <button style={styles.btn} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.body}>
        <div style={styles.chatPane}>
          <MessageList messages={messages} isStreaming={isStreaming} />
          {error && <div style={styles.errorBar}>{error}</div>}
          <ChatBox onSend={sendMessage} disabled={isStreaming} />
        </div>

        {showDashboard && (
          <DashboardEmbed
            url={activeDashboardUrl}
            onClose={() => setShowDashboard(false)}
          />
        )}
      </div>
    </div>
  );
}