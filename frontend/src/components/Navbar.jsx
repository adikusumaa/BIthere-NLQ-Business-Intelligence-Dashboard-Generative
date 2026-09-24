import { useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import WorkspaceSwitcher from "./WorkspaceSwitcher";
import { useChatStore } from "../store/chatStore";

const MENU = [
  { path: "/chat", label: "Chat" },
  { path: "/datasets", label: "Datasets" },
  { path: "/schema-builder", label: "Schema" },
  { path: "/knowledge-base", label: "Knowledge" },
  { path: "/integrations", label: "Integrations" },
];

export default function Navbar({ rightActions }) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = async () => {
    useChatStore.getState().reset();
    await logout();
    navigate("/login");
  };

  return (
    <header
      style={{
        background: "var(--ios-surface)",
        borderBottom: "1px solid var(--ios-separator)",
        padding: "10px 20px",
        display: "flex",
        alignItems: "center",
        gap: 16,
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            background: "linear-gradient(135deg, #007AFF 0%, #5856D6 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#FFF",
            fontSize: 14,
            fontWeight: 700,
          }}
        >
          B
        </div>
        <div style={{ fontSize: 15, fontWeight: 600 }}>BIthere</div>
      </div>

      <nav style={{ display: "flex", gap: 4, marginLeft: 8 }}>
        {MENU.map((item) => {
          const active = location.pathname.startsWith(item.path);
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                padding: "6px 12px",
                borderRadius: 6,
                border: "none",
                background: active ? "rgba(59,130,246,0.12)" : "transparent",
                color: active ? "var(--ios-blue)" : "var(--ios-text-secondary)",
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              {item.label}
            </button>
          );
        })}
      </nav>

      <div style={{ flex: 1 }} />

      <WorkspaceSwitcher />

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {rightActions}
        {role === "admin" && (
          <button
            onClick={() => navigate("/admin")}
            style={iconBtnStyle}
            title="Admin"
          >
            ⚙
          </button>
        )}
        <div style={{ fontSize: 12, color: "var(--ios-text-secondary)", maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {user?.email}
        </div>
        <button onClick={handleLogout} style={{ ...iconBtnStyle, padding: "6px 12px", borderRadius: 20, width: "auto" }}>
          Logout
        </button>
      </div>
    </header>
  );
}

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