import { useState } from "react";
import { useNavigate } from "react-router-dom";

import ChatBox from "../components/ChatBox";
import DashboardEmbed from "../components/DashboardEmbed";
import MessageList from "../components/MessageList";
import ReportButton from "../components/ReportButton";
import { PanelIcon, UserIcon } from "../components/Icons";
import { useAuthStore } from "../store/authStore";
import { useChatStore } from "../store/chatStore";

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: "var(--ios-bg)",
  },
  header: {
    background: "var(--ios-surface)",
    borderBottom: "1px solid var(--ios-separator)",
    padding: "12px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "16px",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  avatar: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    background: "linear-gradient(135deg, #007AFF 0%, #5856D6 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#FFFFFF",
    fontSize: "15px",
    fontWeight: "700",
    boxShadow: "0 2px 8px rgba(0, 122, 255, 0.24)",
  },
  brandText: {
    display: "flex",
    flexDirection: "column",
    lineHeight: 1.2,
  },
  brandName: {
    fontSize: "17px",
    fontWeight: "600",
    color: "var(--ios-text)",
    letterSpacing: "-0.02em",
  },
  brandTag: {
    fontSize: "12px",
    color: "var(--ios-text-secondary)",
  },
  actions: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  iconBtn: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--ios-surface-2)",
    color: "var(--ios-blue)",
    transition: "background 0.15s ease",
  },
  body: {
    flex: 1,
    display: "flex",
    overflow: "hidden",
    background: "var(--ios-bg)",
  },
  chatPane: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
  },
  errorBar: {
    padding: "10px 20px",
    background: "rgba(255, 59, 48, 0.08)",
    color: "var(--ios-red)",
    borderTop: "1px solid rgba(255, 59, 48, 0.2)",
    fontSize: "13px",
    textAlign: "center",
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

  const handleAdminClick = () => navigate("/admin");

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.brand}>
          <div style={styles.avatar}>
            {user?.email ? user.email[0].toUpperCase() : "B"}
          </div>
          <div style={styles.brandText}>
            <div style={styles.brandName}>BIthere</div>
            <div style={styles.brandTag}>{user?.email || "Analyst"}</div>
          </div>
        </div>

        <div style={styles.actions}>
          <ReportButton
            insight={lastInsight}
            dashboardUrl={activeDashboardUrl}
          />
          {role === "admin" && (
            <button
              style={styles.iconBtn}
              onClick={handleAdminClick}
              title="Admin panel"
            >
              <UserIcon size={18} color="var(--ios-blue)" />
            </button>
          )}
          <button
            style={styles.iconBtn}
            onClick={() => setShowDashboard((v) => !v)}
            title={showDashboard ? "Hide dashboard" : "Show dashboard"}
          >
            <PanelIcon size={18} color="var(--ios-blue)" />
          </button>
          <button
            className="ios-btn-ghost"
            onClick={handleLogout}
            style={{
              padding: "6px 12px",
              fontSize: "14px",
              borderRadius: "var(--radius-pill)",
            }}
          >
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