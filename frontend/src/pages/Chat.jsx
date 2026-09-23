import { useState } from "react";

import ChatBox from "../components/ChatBox";
import DashboardEmbed from "../components/DashboardEmbed";
import MessageList from "../components/MessageList";
import Navbar from "../components/Navbar";
import ReportButton from "../components/ReportButton";
import { useChatStore } from "../store/chatStore";

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    background: "var(--ios-bg)",
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

const iconBtnStyle = {
  width: 32,
  height: 32,
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "var(--ios-surface-2)",
  color: "var(--ios-blue)",
  border: "none",
  fontSize: 14,
  cursor: "pointer",
};

export default function Chat() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);
  const activeDashboardUrl = useChatStore((s) => s.activeDashboardUrl);
  const activeDashboardMetabaseId = useChatStore((s) => s.activeDashboardMetabaseId);
  const sendMessage = useChatStore((s) => s.sendMessage);

  const [showDashboard, setShowDashboard] = useState(true);

  const lastInsight = (() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].role === "assistant" && messages[i].insight) {
        return messages[i].insight;
      }
    }
    return null;
  })();

  return (
    <div style={styles.page}>
      <Navbar
        rightActions={
          <>
            <ReportButton
              insight={lastInsight}
              dashboardUrl={activeDashboardUrl}
            />
            <button
              style={iconBtnStyle}
              onClick={() => setShowDashboard((v) => !v)}
              title={showDashboard ? "Hide dashboard" : "Show dashboard"}
            >
              ▤
            </button>
          </>
        }
      />

      <div style={styles.body}>
        <div style={styles.chatPane}>
          <MessageList messages={messages} isStreaming={isStreaming} />
          {error && <div style={styles.errorBar}>{error}</div>}
          <ChatBox onSend={sendMessage} disabled={isStreaming} />
        </div>

        {showDashboard && (
          <DashboardEmbed
            url={activeDashboardUrl}
            metabaseId={activeDashboardMetabaseId}
            onClose={() => setShowDashboard(false)}
          />
        )}
      </div>
    </div>
  );
}